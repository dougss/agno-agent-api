from typing import Dict, Any, Optional, List
import json
import importlib
from datetime import datetime
import asyncio
import logging
from contextlib import contextmanager

from agno.agent import Agent
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory
from agno.vectordb.pgvector import PgVector, SearchType
from agno.knowledge.url import UrlKnowledge
from agno.embedder.openai import OpenAIEmbedder

from db.session import get_db, db_url, SessionLocal
from db.models import DynamicAgent, AgentSpecification, DynamicKnowledgeBase
from core.provider_manager import provider_manager

logger = logging.getLogger(__name__)


class AgentSpecificationValidator:
    """Validador de especificações de agentes"""
    
    REQUIRED_FIELDS = [
        "agent_config.name",
        "agent_config.slug", 
        "agent_config.description",
        "model_config.model_id",
        "instructions.system_message"
    ]
    
    AVAILABLE_TOOLS = {
        "DuckDuckGoTools": "agno.tools.duckduckgo.DuckDuckGoTools",
        "YFinanceTools": "agno.tools.yfinance.YFinanceTools", 
        "ReasoningTools": "agno.tools.reasoning.ReasoningTools",
        "KnowledgeTools": "agno.tools.knowledge.KnowledgeTools"
    }
    
    def validate_specification(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """
        Valida uma especificação de agente
        
        Returns:
            Dict com is_valid, errors, warnings, score
        """
        errors = []
        warnings = []
        
        # Validar campos obrigatórios
        for field_path in self.REQUIRED_FIELDS:
            if not self._get_nested_value(spec, field_path):
                errors.append(f"Campo obrigatório ausente: {field_path}")
        
        # Validar tools
        tools_config = spec.get("tools_config", [])
        for tool in tools_config:
            tool_name = tool.get("name")
            if tool_name not in self.AVAILABLE_TOOLS:
                warnings.append(f"Tool não reconhecida: {tool_name}")
        
        # Validar configuração do modelo
        model_config = spec.get("model_config", {})
        if model_config.get("temperature", 0.7) > 1.0:
            warnings.append("Temperature alta pode gerar respostas inconsistentes")
        
        # Calcular score de qualidade (0-100)
        score = self._calculate_quality_score(spec, errors, warnings)
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "score": score
        }
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Obtém valor usando path com pontos (ex: 'agent_config.name')"""
        keys = path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        return value
    
    def _calculate_quality_score(self, spec: Dict, errors: List, warnings: List) -> int:
        """Calcula score de qualidade da especificação"""
        base_score = 100
        
        # Penalidades
        base_score -= len(errors) * 20  # Erros são críticos
        base_score -= len(warnings) * 5  # Warnings são moderados
        
        # Bônus por completude
        agent_config = spec.get("agent_config", {})
        if agent_config.get("role"):
            base_score += 5
        if agent_config.get("specialization"):
            base_score += 5
        
        # Bônus por instruções detalhadas
        instructions = spec.get("instructions", {})
        if instructions.get("guidelines"):
            base_score += 10
        if instructions.get("examples"):
            base_score += 10
        
        # Bônus por knowledge base
        if spec.get("knowledge_base", {}).get("enabled"):
            base_score += 15
        
        return max(0, min(100, base_score))


class DynamicAgentFactory:
    """Factory para criar e carregar agentes dinamicamente"""
    
    def __init__(self):
        self.validator = AgentSpecificationValidator()
    
    @contextmanager
    def get_db_session(self):
        """Context manager para sessões do banco"""
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    async def create_agent_from_specification(
        self, 
        specification: Dict[str, Any],
        created_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Cria um agente a partir de uma especificação validada
        
        Returns:
            Dict com agent_id, status, validation_result
        """
        
        # 1. Validar especificação
        validation_result = self.validator.validate_specification(specification)
        
        if not validation_result["is_valid"]:
            return {
                "success": False,
                "validation_result": validation_result,
                "error": "Especificação inválida"
            }
        
        try:
            # 2. Salvar especificação no banco
            spec_id = await self._save_specification(specification, created_by)
            
            # 3. Criar knowledge base se necessário
            kb_config = None
            if specification.get("knowledge_base", {}).get("enabled"):
                kb_config = await self._create_knowledge_base(specification)
            
            # 4. Inserir agente no banco
            agent_id = await self._insert_agent_record(specification, kb_config, created_by)
            
            # 5. Atualizar especificação com agent_id
            await self._update_specification_status(spec_id, "created", agent_id)
            
            # 6. Teste básico de criação
            test_result = await self._test_agent_creation(agent_id)
            
            return {
                "success": True,
                "agent_id": agent_id,
                "specification_id": spec_id,
                "validation_result": validation_result,
                "test_result": test_result,
                "knowledge_base": kb_config
            }
            
        except Exception as e:
            logger.error(f"Erro criando agente: {e}")
            return {
                "success": False,
                "error": str(e),
                "validation_result": validation_result
            }
    
    async def load_dynamic_agent(
        self,
        agent_id: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> Agent:
        """
        Carrega um agente dinâmico do banco de dados
        """
        
        # 1. Buscar configuração do agente
        agent_config = await self._get_agent_config(agent_id)
        
        if not agent_config:
            raise ValueError(f"Agente {agent_id} não encontrado")
        
        # 2. Configurar modelo
        model_config = agent_config["model_config"]
        provider = model_config.get("provider", "openai")
        model_id = model_config["model_id"]
        
        model = provider_manager.create_model(
            provider, 
            model_id,
            max_tokens=model_config.get("max_tokens", 2000),
            temperature=model_config.get("temperature", 0.7)
        )
        
        if not model:
            # Fallback to OpenAI if provider fails
            logger.warning(f"Failed to create model with provider {provider}, falling back to OpenAI")
            model = provider_manager.create_model("openai", "gpt-4o")
        
        # 3. Configurar tools
        tools = []
        for tool_config in agent_config["tools_config"]:
            if tool_config.get("enabled", True):
                tool_class = self._load_tool_class(tool_config["name"])
                if tool_class:
                    tool_instance = tool_class(**tool_config.get("config", {}))
                    tools.append(tool_instance)
        
        # 4. Configurar knowledge base
        knowledge = None
        if agent_config.get("knowledge_enabled"):
            knowledge = await self._load_agent_knowledge(agent_id)
        
        # 5. Configurar memória
        memory = None
        if agent_config.get("memory_enabled"):
            memory = Memory(
                model=model,
                db=PostgresMemoryDb(
                    table_name=f"agent_{agent_id}_memories",
                    db_url=db_url
                ),
                delete_memories=True,
                clear_memories=True,
            )
        
        # 6. Criar instância do agente
        agent = Agent(
            name=agent_config["name"],
            agent_id=agent_id,
            user_id=user_id,
            session_id=session_id,
            model=model,
            tools=tools,
            description=agent_config["description"],
            instructions=agent_config["instructions"]["system_message"],
            knowledge=knowledge,
            search_knowledge=knowledge is not None,
            memory=memory,
            enable_agentic_memory=memory is not None,
            reasoning=agent_config.get("reasoning_enabled", False),
            storage=PostgresAgentStorage(
                table_name=f"agent_{agent_id}_sessions",
                db_url=db_url
            ),
            add_history_to_messages=True,
            num_history_runs=3,
            read_chat_history=True,
            markdown=agent_config.get("markdown", True),
            add_datetime_to_instructions=True,
            debug_mode=True
        )
        
        # 7. Atualizar métricas de uso
        await self._update_agent_usage(agent_id)
        
        return agent
    
    async def _save_specification(self, spec: Dict, created_by: str) -> str:
        """Salva especificação no banco"""
        with self.get_db_session() as db:
            specification = AgentSpecification(
                specification=spec,
                created_by=created_by
            )
            db.add(specification)
            db.commit()
            db.refresh(specification)
            return str(specification.id)
    
    async def _create_knowledge_base(self, spec: Dict) -> Dict:
        """Cria knowledge base para o agente"""
        kb_config = spec.get("knowledge_base", {})
        
        if kb_config.get("type") == "url":
            sources = kb_config.get("sources", [])
            if sources:
                # Configuração será usada posteriormente na criação do agente
                return {
                    "type": "url",
                    "sources": sources,
                    "table_name": f"kb_{spec['agent_config']['slug']}",
                    "status": "configured"
                }
        
        return None
    
    async def _insert_agent_record(self, spec: Dict, kb_config: Dict, created_by: str) -> str:
        """Insere registro do agente no banco"""
        agent_config = spec["agent_config"]
        
        with self.get_db_session() as db:
            agent = DynamicAgent(
                name=agent_config["name"],
                slug=agent_config["slug"],
                description=agent_config["description"],
                role=agent_config.get("role"),
                specialization=agent_config.get("specialization"),
                model_config=spec["model_config"],
                tools_config=spec["tools_config"],
                instructions=spec["instructions"],
                reasoning_enabled=spec.get("features", {}).get("reasoning_enabled", False),
                memory_enabled=spec.get("features", {}).get("memory_enabled", True),
                knowledge_enabled=spec.get("features", {}).get("knowledge_enabled", False),
                created_by=created_by
            )
            
            db.add(agent)
            db.commit()
            db.refresh(agent)
            
            # Criar knowledge base se configurada
            if kb_config:
                kb = DynamicKnowledgeBase(
                    agent_id=agent.id,
                    name=kb_config.get("name", f"kb_{agent.slug}"),
                    type=kb_config.get("type", "url"),
                    sources=kb_config.get("sources", []),
                    vector_config=kb_config.get("vector_config", {})
                )
                db.add(kb)
                db.commit()
            
            return str(agent.id)
    
    async def _get_agent_config(self, agent_id: str) -> Optional[Dict]:
        """Busca configuração do agente no banco"""
        with self.get_db_session() as db:
            agent = db.query(DynamicAgent).filter(
                DynamicAgent.id == agent_id,
                DynamicAgent.status == "active"
            ).first()
            
            if agent:
                return {
                    "id": str(agent.id),
                    "name": agent.name,
                    "slug": agent.slug,
                    "description": agent.description,
                    "role": agent.role,
                    "specialization": agent.specialization,
                    "model_config": agent.model_config,
                    "tools_config": agent.tools_config,
                    "instructions": agent.instructions,
                    "reasoning_enabled": agent.reasoning_enabled,
                    "memory_enabled": agent.memory_enabled,
                    "knowledge_enabled": agent.knowledge_enabled,
                    "status": agent.status,
                    "created_by": agent.created_by,
                    "created_at": agent.created_at,
                    "updated_at": agent.updated_at,
                    "total_sessions": agent.total_sessions,
                    "avg_response_time_ms": agent.avg_response_time_ms,
                    "success_rate": agent.success_rate,
                    "last_used_at": agent.last_used_at
                }
            return None
    
    def _load_tool_class(self, tool_name: str):
        """Carrega classe de tool dinamicamente"""
        tool_mapping = self.validator.AVAILABLE_TOOLS
        if tool_name in tool_mapping:
            module_path, class_name = tool_mapping[tool_name].rsplit('.', 1)
            module = importlib.import_module(module_path)
            return getattr(module, class_name)
        return None
    
    async def _load_agent_knowledge(self, agent_id: str):
        """Carrega knowledge base do agente"""
        # Implementação futura para carregar knowledge base específica
        return None
    
    async def _update_specification_status(self, spec_id: str, status: str, agent_id: str = None):
        """Atualiza status da especificação"""
        with self.get_db_session() as db:
            spec = db.query(AgentSpecification).filter(
                AgentSpecification.id == spec_id
            ).first()
            
            if spec:
                spec.status = status
                if agent_id:
                    spec.created_agent_id = agent_id
                spec.updated_at = datetime.now()
                db.commit()
    
    async def _test_agent_creation(self, agent_id: str) -> Dict:
        """Testa criação básica do agente"""
        try:
            agent = await self.load_dynamic_agent(agent_id)
            return {
                "success": True,
                "message": "Agente criado e testado com sucesso"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _update_agent_usage(self, agent_id: str):
        """Atualiza métricas de uso do agente"""
        with self.get_db_session() as db:
            agent = db.query(DynamicAgent).filter(
                DynamicAgent.id == agent_id
            ).first()
            
            if agent:
                agent.last_used_at = datetime.now()
                agent.total_sessions += 1
                db.commit()


# Instância global do factory
agent_factory = DynamicAgentFactory()
