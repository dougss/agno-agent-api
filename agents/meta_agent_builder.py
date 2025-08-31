from textwrap import dedent
from typing import Optional, Dict, Any, List
import json
import re
from datetime import datetime

from agno.agent import Agent, AgentKnowledge
from agno.embedder.openai import OpenAIEmbedder
from agno.knowledge.url import UrlKnowledge
from agno.memory.v2.db.postgres import PostgresMemoryDb
from agno.memory.v2.memory import Memory
from agno.storage.agent.postgres import PostgresAgentStorage
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.knowledge import KnowledgeTools
from agno.vectordb.pgvector import PgVector, SearchType

from db.session import db_url
from core.provider_manager import provider_manager
from core.template_manager import template_manager
from core.intelligent_validation import intelligent_validator


class AgentResearchTools:
    """Custom tools para pesquisa de domínios e criação de agentes"""
    
    def research_domain_expertise(self, domain: str) -> Dict[str, Any]:
        """Pesquisa conhecimento específico do domínio"""
        # Implementação de pesquisa especializada
        domain_expertise = {
            "marketing": {
                "key_areas": ["SEO", "Content Marketing", "Social Media", "Analytics"],
                "tools_needed": ["DuckDuckGoTools", "CalculatorTools"],
                "knowledge_sources": ["https://blog.hubspot.com", "https://marketingland.com"]
            },
            "finance": {
                "key_areas": ["Investment Analysis", "Market Research", "Financial Planning"],
                "tools_needed": ["YFinanceTools", "DuckDuckGoTools"],
                "knowledge_sources": ["https://www.investopedia.com", "https://finance.yahoo.com"]
            },
            "legal": {
                "key_areas": ["Legal Research", "Compliance", "Document Analysis"],
                "tools_needed": ["DuckDuckGoTools", "CalculatorTools"],
                "knowledge_sources": ["https://www.law.com", "https://www.americanbar.org"]
            },
            "technology": {
                "key_areas": ["Software Development", "Architecture", "Best Practices"],
                "tools_needed": ["GitHubTools", "DuckDuckGoTools"],
                "knowledge_sources": ["https://github.com", "https://stackoverflow.com"]
            }
        }
        
        return domain_expertise.get(domain.lower(), {
            "key_areas": ["General Knowledge"],
            "tools_needed": ["DuckDuckGoTools"],
            "knowledge_sources": []
        })
    
    def recommend_tools_for_domain(self, domain: str) -> List[str]:
        """Sugere tools apropriadas para o domínio"""
        tool_recommendations = {
            "marketing": ["DuckDuckGoTools", "CalculatorTools"],
            "finance": ["YFinanceTools", "DuckDuckGoTools", "CalculatorTools"],
            "legal": ["DuckDuckGoTools", "CalculatorTools"],
            "technology": ["GitHubTools", "DuckDuckGoTools"],
            "healthcare": ["DuckDuckGoTools", "CalculatorTools"]
        }
        return tool_recommendations.get(domain.lower(), ["DuckDuckGoTools"])
    
    def analyze_existing_agents(self, specialization: str) -> Dict[str, Any]:
        """Analisa agentes similares existentes"""
        # Implementação de análise comparativa
        return {
            "similar_agents": [],
            "recommendations": f"Para {specialization}, considere incluir reasoning e knowledge base"
        }
    
    def generate_test_scenarios(self, agent_spec: Dict) -> List[Dict]:
        """Gera cenários de teste para o agente"""
        specialization = agent_spec.get("agent_config", {}).get("specialization", "general tasks")
        
        return [
            {
                "scenario": "Basic interaction test",
                "input": f"Hello, can you help me with {specialization}?",
                "expected_behavior": "Friendly introduction and capability overview"
            },
            {
                "scenario": "Domain expertise test", 
                "input": f"What are the key challenges in {specialization}?",
                "expected_behavior": "Detailed domain-specific insights"
            },
            {
                "scenario": "Tool usage test",
                "input": f"Can you search for recent information about {specialization}?",
                "expected_behavior": "Uses appropriate tools to gather information"
            }
        ]


class ValidationTools:
    """Tools para validação de especificações de agentes"""
    
    def validate_agent_specification(self, user_input: str, specification: Dict, domain: str = None, use_case: str = None) -> Dict[str, Any]:
        """Valida uma especificação de agente usando o sistema de validação"""
        try:
            # Use the intelligent validator
            validation_result = intelligent_validator.validate_specification_intelligently(
                user_input=user_input,
                specification=specification,
                domain=domain,
                use_case=use_case
            )
            
            # Generate improvement suggestions
            suggestions_text = "\n".join(validation_result["suggestions"])
            
            return {
                "validation_result": validation_result,
                "improvement_suggestions": suggestions_text,
                "is_valid": validation_result["is_valid"],
                "score": validation_result["score"],
                "issues_count": len(validation_result["issues"]),
                "suggestions_count": len(validation_result["suggestions"])
            }
        except Exception as e:
            return {
                "error": f"Erro na validação: {str(e)}",
                "is_valid": False,
                "score": 0
            }
    
    def improve_specification(self, specification: Dict, issues: List[str], suggestions: List[str]) -> Dict[str, Any]:
        """Melhora uma especificação baseada nos problemas identificados"""
        improved_spec = specification.copy()
        
        # Apply common improvements
        for suggestion in suggestions:
            if "adicionar" in suggestion.lower() and "yfinancetools" in suggestion.lower():
                # Add YFinanceTools if missing for finance domain
                tools_config = improved_spec.get("tools_config", [])
                if not any(tool.get("name") == "YFinanceTools" for tool in tools_config):
                    tools_config.append({
                        "name": "YFinanceTools",
                        "enabled": True,
                        "config": {}
                    })
                    improved_spec["tools_config"] = tools_config
            
            elif "adicionar" in suggestion.lower() and "calculatortools" in suggestion.lower():
                # Add CalculatorTools if missing for finance domain
                tools_config = improved_spec.get("tools_config", [])
                if not any(tool.get("name") == "CalculatorTools" for tool in tools_config):
                    tools_config.append({
                        "name": "CalculatorTools",
                        "enabled": True,
                        "config": {}
                    })
                    improved_spec["tools_config"] = tools_config
            
            elif "substituir" in suggestion.lower() and "placeholders" in suggestion.lower():
                # Replace generic knowledge sources
                knowledge_config = improved_spec.get("knowledge_base", {})
                if knowledge_config.get("enabled", False):
                    # Replace generic sources with real ones
                    knowledge_config["sources"] = [
                        "https://www.investopedia.com",
                        "https://finance.yahoo.com",
                        "https://www.b3.com.br"
                    ]
                    improved_spec["knowledge_base"] = knowledge_config
            
            elif "brasileiro" in suggestion.lower():
                # Replace American sources with Brazilian ones
                knowledge_config = improved_spec.get("knowledge_base", {})
                if knowledge_config.get("enabled", False):
                    knowledge_config["sources"] = [
                        "https://www.infomoney.com.br",
                        "https://www.xpresearch.com.br",
                        "https://www.b3.com.br",
                        "https://www.cvm.gov.br"
                    ]
                    improved_spec["knowledge_base"] = knowledge_config
                
                # Replace American tools with appropriate ones
                tools_config = improved_spec.get("tools_config", [])
                tools_config = [tool for tool in tools_config if tool.get("name") not in ["MintAPI", "PlaidAPI"]]
                
                # Add appropriate tools for Brazilian market
                if not any(tool.get("name") == "YFinanceTools" for tool in tools_config):
                    tools_config.append({
                        "name": "YFinanceTools",
                        "enabled": True,
                        "config": {}
                    })
                
                improved_spec["tools_config"] = tools_config
        
        return {
            "improved_specification": improved_spec,
            "improvements_applied": len(suggestions),
            "original_score": 0,  # Would need to calculate
            "estimated_improvement": "Significant"
        }


class KnowledgeBuilderTools:
    """Tools para criação automática de knowledge bases"""
    
    def create_domain_knowledge_base(self, domain: str, agent_id: str) -> Dict[str, Any]:
        """Cria knowledge base automaticamente para o domínio"""
        knowledge_sources = self.recommend_knowledge_sources(domain)
        
        # Configuração da knowledge base
        kb_config = {
            "name": f"{domain}_knowledge_base",
            "sources": knowledge_sources,
            "vector_db": {
                "table_name": f"kb_{agent_id}",
                "search_type": "hybrid"
            }
        }
        
        return kb_config
    
    def recommend_knowledge_sources(self, domain: str) -> List[str]:
        """Sugere fontes de conhecimento por domínio"""
        domain_sources = {
            "marketing": [
                "https://blog.hubspot.com",
                "https://marketingland.com", 
                "https://contentmarketinginstitute.com"
            ],
            "finance": [
                "https://www.investopedia.com",
                "https://finance.yahoo.com",
                "https://www.bloomberg.com"
            ],
            "legal": [
                "https://www.law.com",
                "https://www.americanbar.org",
                "https://www.justia.com"
            ],
            "technology": [
                "https://github.com",
                "https://stackoverflow.com",
                "https://docs.python.org"
            ]
        }
        return domain_sources.get(domain.lower(), [])


def get_meta_agent_knowledge() -> AgentKnowledge:
    """Knowledge base específica para criação de agentes"""
    return UrlKnowledge(
        urls=[
            "https://docs.agno.com/llms-full.txt",
            "https://docs.agno.com/agents/introduction.md",
            "https://docs.agno.com/tools/introduction.md",
            "https://docs.agno.com/reasoning/introduction.md"
        ],
        vector_db=PgVector(
            db_url=db_url,
            table_name="meta_agent_knowledge",
            search_type=SearchType.hybrid,
            embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        ),
    )


def get_meta_agent_builder(
    provider: str = "openai",
    model_id: str = "gpt-4o",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None,
    debug_mode: bool = True,
) -> Agent:
    """
    Meta-Agente especializado em criar outros agentes através de conversação natural
    """
    
    # Instanciar tools customizadas
    agent_research_tools = AgentResearchTools()
    knowledge_builder_tools = KnowledgeBuilderTools()
    
    # Create model using provider manager
    model = provider_manager.create_model(provider, model_id)
    if not model:
        # Fallback to OpenAI if provider fails
        logger.warning(f"Failed to create model with provider {provider}, falling back to OpenAI")
        model = provider_manager.create_model("openai", "gpt-4o")
    
    return Agent(
        name="Meta-Agent Builder",
        agent_id="meta_agent_builder", 
        user_id=user_id,
        session_id=session_id,
        model=model,
        
        # Tools especializadas para criação de agentes
                tools=[
            DuckDuckGoTools(),
            ReasoningTools(
                think=True,
                analyze=True,
                add_instructions=True,
                add_few_shot=True
            ),
            KnowledgeTools(
                knowledge=get_meta_agent_knowledge(),
                think=True,
                search=True,
                analyze=True
            ),
            ValidationTools()
        ],
        
        # Descrição especializada
        description=dedent("""\
            Você é o Meta-Agent Builder, um especialista em criação de agentes de IA usando o framework Agno.
            
            Sua missão é ajudar usuários a criar agentes especializados através de conversação natural,
            fazendo as perguntas certas para entender necessidades e gerando especificações completas.
        """),
        
        # Instruções detalhadas para criação de agentes
        instructions=dedent("""\
            Seu processo de criação de agentes segue estas etapas estruturadas:

            ## 1. DISCOVERY & ANÁLISE (Sempre começar aqui)
            
            Primeiro, faça perguntas estratégicas para entender:
            - **Domínio/Especialização**: Em que área o agente vai atuar?
            - **Casos de Uso**: Que tipos de tarefas ele deve resolver?
            - **Audiência**: Quem vai interagir com este agente?
            - **Complexidade**: Tarefas simples ou análises complexas?
            - **Integração**: Precisa de tools específicas ou dados externos?
            
            Use o reasoning tool para pensar sobre as necessidades identificadas.

            ## 2. RESEARCH PHASE
            
            Após entender as necessidades:
            - Use search_knowledge para pesquisar padrões do Agno relevantes
            - Pesquise melhores práticas para o domínio específico 
            - Identifique tools apropriadas para as tarefas
            - Analise exemplos similares na documentação
            
            ## 3. TEMPLATE RECOMMENDATION
            
            Primeiro, verifique se existe um template adequado para o domínio:
            - Use o template system para recomendações automáticas
            - Se um template existir, sugira seu uso com customizações
            - Se não existir, crie uma especificação personalizada
            
            ## 4. DESIGN & SPECIFICATION
            
            Crie uma especificação completa seguindo este template JSON:
            
            ```json
            {
                "agent_config": {
                    "name": "Nome Descritivo",
                    "slug": "nome_slug_unico", 
                    "description": "Descrição clara em 2-3 frases",
                    "role": "Papel específico do agente",
                    "specialization": "Área de especialização"
                },
                "model_config": {
                    "provider": "openai",
                    "model_id": "gpt-4o-mini",  # Modelo mais eficiente para agentes especializados
                    "max_tokens": 2000,
                    "temperature": 0.7
                },
                "tools_config": [
                    {
                        "name": "DuckDuckGoTools",
                        "enabled": true,
                        "config": {}
                    }
                ],
                "instructions": {
                    "system_message": "Você é um...",
                    "guidelines": [
                        "Sempre...",
                        "Nunca...", 
                        "Quando..."
                    ],
                    "examples": [
                        {
                            "input": "exemplo de entrada",
                            "output": "exemplo de resposta"
                        }
                    ]
                },
                "features": {
                    "reasoning_enabled": false,
                    "memory_enabled": true,
                    "knowledge_enabled": true,
                    "markdown": true
                },
                "knowledge_base": {
                    "enabled": true,
                    "sources": ["url1", "url2"],
                    "type": "url"
                },
                "validation": {
                    "test_scenarios": [
                        {
                            "input": "Teste 1",
                            "expected_behavior": "Comportamento esperado"
                        }
                    ]
                }
            }
            ```

            ## 5. VALIDATION & REFINEMENT
            
            **IMPORTANTE: Sempre valide a especificação antes de finalizar!**
            
            Após criar a especificação:
            1. **Validação Automática**: Use o sistema de validação para verificar:
               - Contexto do usuário preservado
               - Tools apropriadas recomendadas
               - Knowledge base específica (não genérica)
               - Sem placeholders ou conteúdo fake
            
            2. **Análise de Qualidade**:
               - Verifique se todos os requisitos do usuário foram atendidos
               - Confirme se as tools são reais e funcionais
               - Valide se a knowledge base tem fontes específicas
            
            3. **Refinamento**:
               - Se a validação falhar, corrija os problemas identificados
               - Melhore a especificação baseado no feedback
               - Revalide até atingir qualidade aceitável
            
            4. **Confirmação Final**:
               - Apresente a especificação validada
               - Mostre a pontuação de qualidade
               - Confirme com o usuário antes de prosseguir
            
            ## 6. MODEL SELECTION STRATEGY
            
            Escolha o modelo baseado no tipo de agente:
            
            **gpt-4o-mini** (Recomendado para maioria):
            - Agentes especializados (financeiro, técnico, etc.)
            - Análises rápidas e precisas
            - Custo-benefício otimizado
            
            **gpt-4o** (Para casos complexos):
            - Agentes que precisam de raciocínio avançado
            - Análises criativas e inovadoras
            - Quando precisar de máxima qualidade
            
            **gpt-3.5-turbo** (Para tarefas simples):
            - Agentes de suporte básico
            - Tarefas repetitivas
            - Quando custo é prioridade
            
            ## 7. KNOWLEDGE BASE RECOMMENDATIONS
            
            Para agentes que precisam de conhecimento específico:
            - Sugira fontes relevantes para o domínio
            - Explique como a knowledge base melhorará o agente
            - Ofereça templates de conhecimento por área
            
            ## TEMPLATE INTEGRATION:
            
            - **Sempre verifique templates disponíveis** antes de criar especificações do zero
            - **Sugira templates apropriados** baseado no domínio identificado
            - **Ofereça customizações** para templates existentes
            - **Use templates como base** para especificações personalizadas
            
            ## DIRETRIZES IMPORTANTES:
            
            - **Sempre pergunte antes de assumir** requisitos
            - **Use reasoning tool** para análises complexas
            - **Cite a documentação** Agno quando relevante
            - **Seja específico** em especificações técnicas
            - **Valide** cada etapa com o usuário
            - **Ofereça alternativas** quando apropriado
            
            ## FORMATO DE RESPOSTA:
            
            Quando apresentar a especificação final, use este formato:
            
            ---
            # 🤖 ESPECIFICAÇÃO DO AGENTE: [Nome]
            
            ## 📋 Resumo
            [Breve descrição do agente e capabilities]
            
            ## 🔧 Especificação Técnica
            ```json
            [JSON da especificação completa]
            ```
            
            ## 🧪 Cenários de Teste
            [Lista de testes sugeridos]
            
            ## 💡 Próximos Passos
            [O que fazer após criação]
            ---
            
            Lembre-se: Seu objetivo é criar agentes úteis, bem especificados e que realmente atendam às necessidades do usuário.
        """),
        
        # Configurações avançadas
        knowledge=get_meta_agent_knowledge(),
        search_knowledge=True,
        
        # Reasoning habilitado para decisões complexas
        reasoning=True,
        reasoning_min_steps=2,
        reasoning_max_steps=6,
        
        # Storage e memória
        storage=PostgresAgentStorage(table_name="meta_agent_sessions", db_url=db_url),
        memory=Memory(
            model=model,
            db=PostgresMemoryDb(table_name="meta_agent_memories", db_url=db_url),
            delete_memories=True,
            clear_memories=True,
        ),
        enable_agentic_memory=True,
        
        # Histórico e contexto
        add_history_to_messages=True,
        num_history_runs=3,
        read_chat_history=True,
        
        # Output e debug
        markdown=True,
        show_tool_calls=True,
        add_datetime_to_instructions=True,
        debug_mode=debug_mode,
    )
