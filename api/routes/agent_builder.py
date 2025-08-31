from typing import Optional, Dict, Any
from logging import getLogger
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json
import re

from agents.meta_agent_builder import get_meta_agent_builder
from core.dynamic_agent_factory import agent_factory
from core.provider_manager import provider_manager
from core.template_manager import template_manager

from core.intelligent_validation import intelligent_validator
from core.enhanced_tools import ENHANCED_TOOLS

logger = getLogger(__name__)

agent_builder_router = APIRouter(prefix="/agent-builder", tags=["Agent Builder"])


class ChatRequest(BaseModel):
    """Request para chat com meta-agente"""
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    stream: bool = True
    provider: Optional[str] = "openai"
    model_id: Optional[str] = None


class ParseSpecificationRequest(BaseModel):
    """Request para parse de especificação"""
    response_text: str


class CreateAgentRequest(BaseModel):
    """Request para criação de agente"""
    specification: Dict[str, Any]
    created_by: Optional[str] = None


class CreateFromTemplateRequest(BaseModel):
    """Request para criação de agente a partir de template"""
    template: str
    customizations: Optional[Dict[str, Any]] = None
    created_by: Optional[str] = None


class RecommendTemplateRequest(BaseModel):
    """Request para recomendação de template"""
    description: str


class RecommendToolsRequest(BaseModel):
    """Request para recomendação de tools"""
    domain: str
    use_case: str
    complexity: Optional[str] = "medium"


class ValidateSpecificationRequest(BaseModel):
    """Request para validação de especificação"""
    user_input: str
    specification: Dict[str, Any]
    domain: Optional[str] = None
    use_case: Optional[str] = None


class AnalyzeContextRequest(BaseModel):
    """Request para análise de contexto inteligente"""
    user_input: str


@agent_builder_router.post("/chat")
async def chat_with_meta_agent(request: ChatRequest):
    """
    Conversa com o Meta-Agent Builder
    """
    try:
        # Determine model_id if not provided
        if not request.model_id:
            if request.provider == "anthropic":
                request.model_id = "claude-3-5-sonnet-20241022"
            elif request.provider == "google":
                request.model_id = "gemini-1.5-pro"
            else:
                request.model_id = "gpt-4o"
        
        meta_agent = get_meta_agent_builder(
            provider=request.provider,
            model_id=request.model_id,
            user_id=request.user_id,
            session_id=request.session_id
        )
        
        if request.stream:
            # Implementar streaming response
            async def generate_response():
                async for chunk in await meta_agent.arun(request.message, stream=True):
                    yield f"data: {json.dumps({'content': chunk.content, 'type': 'content'})}\n\n"
                    
                    # Se há tool calls, incluir no stream
                    if hasattr(chunk, 'tool_calls') and chunk.tool_calls:
                        for tool_call in chunk.tool_calls:
                            yield f"data: {json.dumps({'tool_call': tool_call, 'type': 'tool_call'})}\n\n"
                    
                    # Se há reasoning steps, incluir no stream  
                    if hasattr(chunk, 'reasoning_steps') and chunk.reasoning_steps:
                        for step in chunk.reasoning_steps:
                            yield f"data: {json.dumps({'reasoning_step': step, 'type': 'reasoning'})}\n\n"
            
            return StreamingResponse(
                generate_response(),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "Connection": "keep-alive"}
            )
        else:
            response = await meta_agent.arun(request.message, stream=False)
            return {
                "content": response.content,
                "tool_calls": getattr(response, 'tool_calls', []),
                "reasoning_steps": getattr(response, 'reasoning_steps', [])
            }
            
    except Exception as e:
        logger.error(f"Erro no chat com meta-agente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@agent_builder_router.post("/validate-specification")
async def validate_agent_specification(request: ValidateSpecificationRequest):
    """
    Valida uma especificação de agente usando o sistema de validação inteligente
    """
    try:
        # Use the intelligent validator
        validation_result = intelligent_validator.validate_specification_intelligently(
            user_input=request.user_input,
            specification=request.specification,
            domain=request.domain,
            use_case=request.use_case
        )
        
        # Format suggestions for display
        suggestions_text = "\n".join(validation_result["suggestions"])
        
        return {
            "validation_result": validation_result,
            "improvement_suggestions": suggestions_text,
            "is_valid": validation_result["is_valid"],
            "score": validation_result["score"],
            "issues_count": len(validation_result["issues"]),
            "suggestions_count": len(validation_result["suggestions"]),
            "context_analysis": validation_result["context_analysis"],
            "confidence_metrics": validation_result["confidence_metrics"],
            "summary": {
                "status": "✅ Válida" if validation_result["is_valid"] else "❌ Precisa melhorias",
                "quality_score": f"{validation_result['score']:.1f}/100",
                "critical_issues": len([issue for issue in validation_result["issues"] if issue["level"] == "critical"]),
                "total_issues": len(validation_result["issues"]),
                "context_detected": validation_result["context_analysis"]["detected_domains"],
                "market_context": validation_result["context_analysis"]["market_context"],
                "complexity_level": validation_result["context_analysis"]["complexity_level"]
            }
        }
        
    except Exception as e:
        logger.error(f"Erro na validação: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@agent_builder_router.post("/analyze-context")
async def analyze_context_intelligently(request: AnalyzeContextRequest):
    """
    Analisa o contexto do usuário de forma inteligente
    """
    try:
        # Use the intelligent context classifier
        context_analysis = intelligent_validator.classify_context_intelligently(request.user_input)
        
        return {
            "context_analysis": context_analysis,
            "detected_domains": context_analysis["detected_domains"],
            "market_context": context_analysis["market_context"],
            "complexity_level": context_analysis["complexity_level"],
            "confidence_scores": context_analysis["confidence_scores"],
            "summary": {
                "primary_domain": context_analysis["detected_domains"][0]["domain"] if context_analysis["detected_domains"] else "general",
                "market": context_analysis["market_context"]["market"] if context_analysis["market_context"] else "global",
                "complexity": context_analysis["complexity_level"],
                "analysis_confidence": "high" if context_analysis["detected_domains"] else "low"
            }
        }
        
    except Exception as e:
        logger.error(f"Erro na análise de contexto: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@agent_builder_router.post("/parse-specification") 
async def parse_agent_specification(request: ParseSpecificationRequest):
    """
    Extrai especificação JSON da resposta do meta-agente
    """
    try:
        # Buscar JSON na resposta usando regex
        json_pattern = r'```json\s*(\{.*?\})\s*```'
        matches = re.findall(json_pattern, request.response_text, re.DOTALL)
        
        if not matches:
            return {
                "success": False,
                "error": "Nenhuma especificação JSON encontrada na resposta"
            }
        
        # Tentar parsear o JSON
        try:
            specification = json.loads(matches[0])
            
            # Validar especificação
            validation_result = agent_factory.validator.validate_specification(specification)
            
            return {
                "success": True,
                "specification": specification,
                "validation": validation_result
            }
            
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"JSON inválido: {str(e)}"
            }
            
    except Exception as e:
        logger.error(f"Erro parsing especificação: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@agent_builder_router.post("/create-agent")
async def create_dynamic_agent(request: CreateAgentRequest):
    """
    Cria um agente dinamicamente a partir da especificação
    """
    try:
        result = await agent_factory.create_agent_from_specification(
            request.specification,
            request.created_by
        )
        
        if result["success"]:
            return {
                "success": True,
                "agent_id": result["agent_id"],
                "message": "Agente criado com sucesso!",
                "validation_score": result["validation_result"]["score"],
                "test_result": result.get("test_result", {})
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Erro desconhecido"),
                "validation_errors": result.get("validation_result", {}).get("errors", [])
            }
            
    except Exception as e:
        logger.error(f"Erro criando agente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@agent_builder_router.get("/templates")
async def get_available_templates():
    """
    Lista templates disponíveis para criação de agentes
    """
    return {
        "templates": template_manager.get_available_templates()
    }


@agent_builder_router.post("/create-from-template")
async def create_agent_from_template(request: CreateFromTemplateRequest):
    """
    Cria um agente a partir de um template com customizações
    """
    try:
        # Generate specification from template
        specification = template_manager.create_from_template(
            request.template,
            request.customizations
        )
        
        if not specification:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Template '{request.template}' não encontrado"
            )
        
        # Create agent using the factory
        result = await agent_factory.create_agent_from_specification(
            specification,
            request.created_by
        )
        
        if result["success"]:
            return {
                "success": True,
                "agent_id": result["agent_id"],
                "template_used": request.template,
                "customizations": request.customizations,
                "message": f"Agente criado com sucesso usando template '{request.template}'!",
                "validation_score": result["validation_result"]["score"]
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Erro desconhecido"),
                "validation_errors": result.get("validation_result", {}).get("errors", [])
            }
            
    except Exception as e:
        logger.error(f"Erro criando agente do template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@agent_builder_router.post("/recommend-template")
async def recommend_template(request: RecommendTemplateRequest):
    """
    Recomenda template baseado na descrição fornecida
    """
    try:
        recommended_template = template_manager.recommend_template(request.description)
        
        if recommended_template:
            template_info = template_manager.get_template(recommended_template)
            return {
                "recommended_template": recommended_template,
                "confidence": "high" if recommended_template else "low",
                "template_info": {
                    "name": template_info.name,
                    "description": template_info.description,
                    "tools": template_info.tools,
                    "customization_options": template_info.customization_options
                } if template_info else None
            }
        else:
            return {
                "recommended_template": None,
                "confidence": "low",
                "message": "Nenhum template específico recomendado. Considere usar um template personalizado."
            }
            
    except Exception as e:
        logger.error(f"Erro recomendando template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@agent_builder_router.post("/recommend-tools")
async def recommend_tools(request: RecommendToolsRequest):
    """
    Recomenda tools baseado no domínio e caso de uso
    """
    try:
        # Tool recommendations by domain and use case - ONLY REAL TOOLS
        tool_recommendations = {
            "finance": {
                "investment_analysis": ["YFinanceTools", "CalculatorTools", "ChartTools"],
                "expense_tracking": ["CalculatorTools", "ChartTools"],
                "portfolio_management": ["YFinanceTools", "CalculatorTools", "ChartTools"],
                "retirement_planning": ["CalculatorTools"]
            },
            "marketing": {
                "content_strategy": ["DuckDuckGoTools"],
                "market_research": ["DuckDuckGoTools", "ChartTools"],
                "campaign_analysis": ["ChartTools"]
            },
            "legal": {
                "legal_research": ["DuckDuckGoTools"],
                "document_analysis": [],
                "compliance_monitoring": []
            },
            "technology": {
                "code_analysis": ["DuckDuckGoTools"],
                "system_monitoring": ["ChartTools"],
                "documentation": ["DuckDuckGoTools"]
            }
        }
        
        domain_tools = tool_recommendations.get(request.domain.lower(), {})
        use_case_tools = domain_tools.get(request.use_case.lower(), [])
        
        # Add complexity-based recommendations
        if request.complexity == "high":
            use_case_tools.extend(["ReasoningTools", "KnowledgeTools"])
        elif request.complexity == "low":
            # Remove complex tools for simple use cases
            use_case_tools = [tool for tool in use_case_tools if tool not in ["ReasoningTools", "KnowledgeTools"]]
        
        # Ensure DuckDuckGoTools is always included for web search
        if "DuckDuckGoTools" not in use_case_tools:
            use_case_tools.insert(0, "DuckDuckGoTools")
        
        return {
            "recommended_tools": use_case_tools,
            "domain": request.domain,
            "use_case": request.use_case,
            "complexity": request.complexity,
            "confidence": "high" if use_case_tools else "low",
            "explanation": f"Tools recomendadas para {request.domain} - {request.use_case} (complexidade: {request.complexity})"
        }
        
    except Exception as e:
        logger.error(f"Erro recomendando tools: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro interno: {str(e)}"
        )


@agent_builder_router.get("/domains")
async def get_supported_domains():
    """
    Lista domínios suportados para criação de agentes
    """
    return {
        "domains": [
            {
                "name": "Marketing",
                "slug": "marketing", 
                "description": "Agentes para marketing digital, SEO, content strategy",
                "tools": ["DuckDuckGoTools", "CalculatorTools"]
            },
            {
                "name": "Finance", 
                "slug": "finance",
                "description": "Agentes para análise financeira e investimentos",
                "tools": ["YFinanceTools", "CalculatorTools", "DuckDuckGoTools"]
            },
            {
                "name": "Legal",
                "slug": "legal", 
                "description": "Agentes para pesquisa jurídica e compliance",
                "tools": ["DuckDuckGoTools", "CalculatorTools"]
            },
            {
                "name": "Technology",
                "slug": "technology",
                "description": "Agentes para desenvolvimento e arquitetura",
                "tools": ["GitHubTools", "DuckDuckGoTools"]
            },
            {
                "name": "Healthcare", 
                "slug": "healthcare",
                "description": "Agentes para pesquisa médica e saúde",
                "tools": ["DuckDuckGoTools", "CalculatorTools"]
            }
        ]
    }


@agent_builder_router.get("/providers")
async def get_available_providers():
    """
    Lista providers e modelos disponíveis
    """
    return {
        "providers": provider_manager.get_all_models(),
        "recommendations": {
            "complex_analysis": provider_manager.get_recommended_model("complex_analysis"),
            "cost_optimization": provider_manager.get_recommended_model("cost_optimization"),
            "general_tasks": provider_manager.get_recommended_model("general_tasks"),
            "creative_tasks": provider_manager.get_recommended_model("creative_tasks")
        }
    }


@agent_builder_router.get("/tools")
async def get_available_tools():
    """
    Lista tools disponíveis para agentes
    """
    return {
        "tools": [
            {
                "name": "DuckDuckGoTools",
                "display_name": "Web Search",
                "description": "Pesquisa na web usando DuckDuckGo",
                "category": "search",
                "config_schema": {}
            },
            {
                "name": "YFinanceTools", 
                "display_name": "Financial Data",
                "description": "Dados financeiros e de ações",
                "category": "finance",
                "config_schema": {
                    "stock_price": "bool",
                    "analyst_recommendations": "bool" 
                }
            },
            {
                "name": "ReasoningTools",
                "display_name": "Reasoning", 
                "description": "Ferramentas de raciocínio estruturado",
                "category": "reasoning",
                "config_schema": {
                    "think": "bool",
                    "analyze": "bool"
                }
            },
            {
                "name": "KnowledgeTools",
                "display_name": "Knowledge Base",
                "description": "Ferramentas para knowledge bases",
                "category": "knowledge",
                "config_schema": {
                    "think": "bool",
                    "search": "bool",
                    "analyze": "bool"
                }
            },

            {
                "name": "CalculatorTools",
                "display_name": "Financial Calculator",
                "description": "Calculadoras financeiras avançadas",
                "category": "finance",
                "config_schema": {
                    "compound_interest": "bool",
                    "portfolio_analysis": "bool",
                    "retirement_planning": "bool"
                }
            },
            {
                "name": "ChartTools",
                "display_name": "Chart Generation",
                "description": "Geração de gráficos e visualizações",
                "category": "visualization",
                "config_schema": {
                    "portfolio_charts": "bool",
                    "expense_trends": "bool"
                }
            },

        ]
    }
