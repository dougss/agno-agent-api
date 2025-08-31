from typing import Dict, Any, List, Optional
import json
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class DomainTemplate:
    """Template for domain-specific agent creation"""
    
    def __init__(
        self,
        name: str,
        slug: str,
        description: str,
        base_config: Dict[str, Any],
        tools: List[str],
        knowledge_sources: List[str],
        examples: List[Dict[str, str]],
        customization_options: Dict[str, Any]
    ):
        self.name = name
        self.slug = slug
        self.description = description
        self.base_config = base_config
        self.tools = tools
        self.knowledge_sources = knowledge_sources
        self.examples = examples
        self.customization_options = customization_options
    
    def generate_specification(self, customizations: Dict[str, Any] = None) -> Dict[str, Any]:
        """Generate agent specification from template with customizations"""
        if customizations is None:
            customizations = {}
        
        # Start with base configuration
        spec = self.base_config.copy()
        
        # Apply customizations
        for key, value in customizations.items():
            if key in self.customization_options:
                if key == "specialization":
                    spec["agent_config"]["specialization"] = value
                    spec["agent_config"]["description"] = f"{self.description} - {value}"
                elif key == "model_config":
                    spec["model_config"].update(value)
                elif key == "tools_config":
                    spec["tools_config"] = value
                elif key == "knowledge_base":
                    spec["knowledge_base"]["sources"] = value
                elif key == "instructions":
                    spec["instructions"]["system_message"] = value
        
        # Generate unique slug
        unique_id = str(uuid.uuid4())[:8]
        spec["agent_config"]["slug"] = f"{spec['agent_config']['slug']}_{unique_id}"
        
        return spec


class TemplateManager:
    """Manager for domain-specific templates"""
    
    def __init__(self):
        self.templates = self._create_templates()
    
    def _create_templates(self) -> Dict[str, DomainTemplate]:
        """Create predefined templates for different domains"""
        
        # Finance Template
        finance_template = DomainTemplate(
            name="Finance Agent",
            slug="finance",
            description="Agente especializado em análise financeira e investimentos",
            base_config={
                "agent_config": {
                    "name": "Agente Financeiro",
                    "slug": "finance_agent",
                    "description": "Agente especializado em análise financeira e investimentos",
                    "role": "Consultor financeiro digital",
                    "specialization": "Análise financeira e investimentos"
                },
                "model_config": {
                    "provider": "openai",
                    "model_id": "gpt-4o-mini",
                    "max_tokens": 2000,
                    "temperature": 0.7
                },
                "tools_config": [
                    {
                        "name": "DuckDuckGoTools",
                        "enabled": True,
                        "config": {}
                    },
                    {
                        "name": "YFinanceTools",
                        "enabled": True,
                        "config": {
                            "stock_price": True,
                            "analyst_recommendations": True
                        }
                    },
                    {
                        "name": "ReasoningTools",
                        "enabled": True,
                        "config": {
                            "think": True,
                            "analyze": True
                        }
                    }
                ],
                "instructions": {
                    "system_message": "Você é um consultor financeiro especializado em análise de investimentos e gestão financeira pessoal. Você ajuda usuários a tomar decisões financeiras informadas, analisar oportunidades de investimento e planejar suas finanças pessoais.",
                    "guidelines": [
                        "Sempre analise o perfil de risco do usuário antes de fazer recomendações",
                        "Forneça explicações claras sobre conceitos financeiros complexos",
                        "Use dados atualizados para suas análises",
                        "Nunca faça promessas de retorno específico",
                        "Sempre considere a diversificação em suas recomendações"
                    ],
                    "examples": [
                        {
                            "input": "Como começar a investir?",
                            "output": "Para começar a investir, primeiro precisamos entender seu perfil financeiro. Vou te ajudar a: 1) Estabelecer uma reserva de emergência, 2) Definir seus objetivos financeiros, 3) Escolher investimentos adequados ao seu perfil de risco."
                        }
                    ]
                },
                "features": {
                    "reasoning_enabled": True,
                    "memory_enabled": True,
                    "knowledge_enabled": True,
                    "markdown": True
                },
                "knowledge_base": {
                    "enabled": True,
                    "sources": [
                        "https://www.investopedia.com",
                        "https://finance.yahoo.com",
                        "https://www.bloomberg.com"
                    ],
                    "type": "url"
                },
                "validation": {
                    "test_scenarios": [
                        {
                            "input": "Como está o mercado de ações hoje?",
                            "expected_behavior": "Fornecer análise atualizada do mercado usando ferramentas de dados financeiros"
                        },
                        {
                            "input": "Quais são os melhores investimentos para iniciantes?",
                            "expected_behavior": "Explicar conceitos básicos e sugerir investimentos adequados ao perfil conservador"
                        }
                    ]
                }
            },
            tools=["DuckDuckGoTools", "YFinanceTools", "ReasoningTools"],
            knowledge_sources=[
                "https://www.investopedia.com",
                "https://finance.yahoo.com", 
                "https://www.bloomberg.com",
                "https://www.xpinc.com/research"
            ],
            examples=[
                {
                    "input": "Analise minha carteira de investimentos",
                    "output": "Vou analisar sua carteira considerando diversificação, risco e alinhamento com seus objetivos."
                },
                {
                    "input": "Como está o mercado de fundos imobiliários?",
                    "output": "Vou pesquisar as tendências atuais do mercado de FIIs e fornecer uma análise detalhada."
                }
            ],
            customization_options={
                "specialization": "string",
                "model_config": "dict",
                "tools_config": "list",
                "knowledge_base": "list",
                "instructions": "string"
            }
        )
        
        # Marketing Template
        marketing_template = DomainTemplate(
            name="Marketing Agent",
            slug="marketing",
            description="Agente especializado em estratégias de marketing digital",
            base_config={
                "agent_config": {
                    "name": "Agente de Marketing",
                    "slug": "marketing_agent",
                    "description": "Agente especializado em estratégias de marketing digital",
                    "role": "Consultor de marketing digital",
                    "specialization": "Marketing digital e estratégias de crescimento"
                },
                "model_config": {
                    "provider": "openai",
                    "model_id": "gpt-4o-mini",
                    "max_tokens": 2000,
                    "temperature": 0.8
                },
                "tools_config": [
                    {
                        "name": "DuckDuckGoTools",
                        "enabled": True,
                        "config": {}
                    },
                    {
                        "name": "ReasoningTools",
                        "enabled": True,
                        "config": {
                            "think": True,
                            "analyze": True
                        }
                    }
                ],
                "instructions": {
                    "system_message": "Você é um especialista em marketing digital com vasta experiência em estratégias de crescimento, SEO, marketing de conteúdo e análise de dados. Você ajuda empresas e profissionais a desenvolver estratégias de marketing eficazes.",
                    "guidelines": [
                        "Sempre considere o público-alvo em suas recomendações",
                        "Use dados e métricas para fundamentar suas sugestões",
                        "Mantenha-se atualizado com as últimas tendências do marketing digital",
                        "Forneça estratégias práticas e implementáveis",
                        "Considere o ROI em todas as recomendações"
                    ],
                    "examples": [
                        {
                            "input": "Como melhorar meu SEO?",
                            "output": "Para melhorar seu SEO, vou analisar: 1) Otimização on-page, 2) Estratégia de conteúdo, 3) Backlinks, 4) Performance técnica. Vou fornecer um plano detalhado."
                        }
                    ]
                },
                "features": {
                    "reasoning_enabled": True,
                    "memory_enabled": True,
                    "knowledge_enabled": True,
                    "markdown": True
                },
                "knowledge_base": {
                    "enabled": True,
                    "sources": [
                        "https://blog.hubspot.com",
                        "https://marketingland.com",
                        "https://moz.com/blog"
                    ],
                    "type": "url"
                },
                "validation": {
                    "test_scenarios": [
                        {
                            "input": "Crie uma estratégia de marketing para meu produto",
                            "expected_behavior": "Desenvolver estratégia completa considerando público-alvo, canais e métricas"
                        }
                    ]
                }
            },
            tools=["DuckDuckGoTools", "ReasoningTools"],
            knowledge_sources=[
                "https://blog.hubspot.com",
                "https://marketingland.com",
                "https://moz.com/blog",
                "https://contentmarketinginstitute.com"
            ],
            examples=[
                {
                    "input": "Desenvolva uma estratégia de conteúdo",
                    "output": "Vou criar uma estratégia de conteúdo baseada no seu público-alvo e objetivos de negócio."
                }
            ],
            customization_options={
                "specialization": "string",
                "model_config": "dict",
                "tools_config": "list",
                "knowledge_base": "list",
                "instructions": "string"
            }
        )
        
        # Legal Template
        legal_template = DomainTemplate(
            name="Legal Agent",
            slug="legal",
            description="Agente especializado em pesquisa jurídica e compliance",
            base_config={
                "agent_config": {
                    "name": "Agente Jurídico",
                    "slug": "legal_agent",
                    "description": "Agente especializado em pesquisa jurídica e compliance",
                    "role": "Assistente de pesquisa jurídica",
                    "specialization": "Pesquisa jurídica e análise legal"
                },
                "model_config": {
                    "provider": "openai",
                    "model_id": "gpt-4o",
                    "max_tokens": 3000,
                    "temperature": 0.3
                },
                "tools_config": [
                    {
                        "name": "DuckDuckGoTools",
                        "enabled": True,
                        "config": {}
                    },
                    {
                        "name": "ReasoningTools",
                        "enabled": True,
                        "config": {
                            "think": True,
                            "analyze": True
                        }
                    }
                ],
                "instructions": {
                    "system_message": "Você é um assistente de pesquisa jurídica especializado em análise legal, compliance e interpretação de leis. Você ajuda profissionais do direito e empresas a navegar questões legais complexas.",
                    "guidelines": [
                        "Sempre cite fontes confiáveis em suas análises",
                        "Destaque a jurisdição relevante para cada questão",
                        "Forneça contexto histórico quando apropriado",
                        "Nunca substitua consulta com advogado qualificado",
                        "Mantenha-se atualizado com mudanças legislativas"
                    ],
                    "examples": [
                        {
                            "input": "Quais são os requisitos para abrir uma empresa?",
                            "output": "Vou analisar os requisitos legais para abertura de empresa, considerando o tipo de sociedade e localização."
                        }
                    ]
                },
                "features": {
                    "reasoning_enabled": True,
                    "memory_enabled": True,
                    "knowledge_enabled": True,
                    "markdown": True
                },
                "knowledge_base": {
                    "enabled": True,
                    "sources": [
                        "https://www.law.com",
                        "https://www.americanbar.org",
                        "https://www.justia.com"
                    ],
                    "type": "url"
                },
                "validation": {
                    "test_scenarios": [
                        {
                            "input": "Analise este contrato",
                            "expected_behavior": "Fornecer análise detalhada dos termos e identificar pontos de atenção"
                        }
                    ]
                }
            },
            tools=["DuckDuckGoTools", "ReasoningTools"],
            knowledge_sources=[
                "https://www.law.com",
                "https://www.americanbar.org",
                "https://www.justia.com"
            ],
            examples=[
                {
                    "input": "Pesquise sobre leis de proteção de dados",
                    "output": "Vou pesquisar as principais leis de proteção de dados e suas implicações para empresas."
                }
            ],
            customization_options={
                "specialization": "string",
                "model_config": "dict",
                "tools_config": "list",
                "knowledge_base": "list",
                "instructions": "string"
            }
        )
        
        # Technology Template
        technology_template = DomainTemplate(
            name="Technology Agent",
            slug="technology",
            description="Agente especializado em desenvolvimento e arquitetura de software",
            base_config={
                "agent_config": {
                    "name": "Agente de Tecnologia",
                    "slug": "technology_agent",
                    "description": "Agente especializado em desenvolvimento e arquitetura de software",
                    "role": "Consultor de tecnologia e desenvolvimento",
                    "specialization": "Desenvolvimento de software e arquitetura"
                },
                "model_config": {
                    "provider": "openai",
                    "model_id": "gpt-4o-mini",
                    "max_tokens": 2000,
                    "temperature": 0.6
                },
                "tools_config": [
                    {
                        "name": "DuckDuckGoTools",
                        "enabled": True,
                        "config": {}
                    },
                    {
                        "name": "ReasoningTools",
                        "enabled": True,
                        "config": {
                            "think": True,
                            "analyze": True
                        }
                    }
                ],
                "instructions": {
                    "system_message": "Você é um especialista em tecnologia com vasta experiência em desenvolvimento de software, arquitetura de sistemas e melhores práticas de programação. Você ajuda desenvolvedores e empresas a resolver problemas técnicos complexos.",
                    "guidelines": [
                        "Sempre considere a escalabilidade em suas recomendações",
                        "Use melhores práticas de segurança em todas as sugestões",
                        "Forneça exemplos de código quando apropriado",
                        "Considere a manutenibilidade do código",
                        "Mantenha-se atualizado com as últimas tecnologias"
                    ],
                    "examples": [
                        {
                            "input": "Como implementar autenticação JWT?",
                            "output": "Vou te mostrar como implementar autenticação JWT de forma segura, incluindo geração de tokens e validação."
                        }
                    ]
                },
                "features": {
                    "reasoning_enabled": True,
                    "memory_enabled": True,
                    "knowledge_enabled": True,
                    "markdown": True
                },
                "knowledge_base": {
                    "enabled": True,
                    "sources": [
                        "https://github.com",
                        "https://stackoverflow.com",
                        "https://docs.python.org"
                    ],
                    "type": "url"
                },
                "validation": {
                    "test_scenarios": [
                        {
                            "input": "Desenvolva uma API REST",
                            "expected_behavior": "Fornecer arquitetura e implementação de API REST seguindo melhores práticas"
                        }
                    ]
                }
            },
            tools=["DuckDuckGoTools", "ReasoningTools"],
            knowledge_sources=[
                "https://github.com",
                "https://stackoverflow.com",
                "https://docs.python.org"
            ],
            examples=[
                {
                    "input": "Analise esta arquitetura de microserviços",
                    "output": "Vou analisar sua arquitetura de microserviços e sugerir melhorias para performance e escalabilidade."
                }
            ],
            customization_options={
                "specialization": "string",
                "model_config": "dict",
                "tools_config": "list",
                "knowledge_base": "list",
                "instructions": "string"
            }
        )
        
        return {
            "finance": finance_template,
            "marketing": marketing_template,
            "legal": legal_template,
            "technology": technology_template
        }
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available templates"""
        templates = []
        for slug, template in self.templates.items():
            templates.append({
                "name": template.name,
                "slug": slug,
                "description": template.description,
                "tools": template.tools,
                "knowledge_sources": template.knowledge_sources,
                "customization_options": template.customization_options
            })
        return templates
    
    def get_template(self, slug: str) -> Optional[DomainTemplate]:
        """Get specific template by slug"""
        return self.templates.get(slug)
    
    def create_from_template(
        self, 
        template_slug: str, 
        customizations: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Create agent specification from template"""
        template = self.get_template(template_slug)
        if not template:
            return None
        
        return template.generate_specification(customizations)
    
    def recommend_template(self, description: str) -> Optional[str]:
        """Recommend template based on description"""
        description_lower = description.lower()
        
        # Simple keyword matching
        if any(word in description_lower for word in ["finance", "invest", "money", "stock", "market"]):
            return "finance"
        elif any(word in description_lower for word in ["marketing", "advertise", "promote", "brand"]):
            return "marketing"
        elif any(word in description_lower for word in ["legal", "law", "contract", "compliance"]):
            return "legal"
        elif any(word in description_lower for word in ["tech", "software", "develop", "code", "program"]):
            return "technology"
        
        return None


# Global template manager instance
template_manager = TemplateManager()
