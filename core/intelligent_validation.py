from typing import Dict, Any, List, Optional, Tuple
import logging
import json
import re
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import asyncio

logger = logging.getLogger(__name__)


class ValidationLevel(Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    level: ValidationLevel
    category: str
    message: str
    suggestion: str
    confidence: float
    context: Dict[str, Any]


class IntelligentValidator:
    """Data-driven intelligent validation system"""
    
    def __init__(self):
        self.tools_registry = self._load_tools_registry()
        self.domain_patterns = self._load_domain_patterns()
        self.context_classifier = self._load_context_classifier()
        self.validation_history = []
        self.learned_rules = {}
    
    def _load_tools_registry(self) -> Dict[str, Any]:
        """Load available tools from Agno framework dynamically"""
        try:
            # This would ideally query Agno's API or documentation
            # For now, we'll use a comprehensive registry
            return {
                "available_tools": [
                    "DuckDuckGoTools", "YFinanceTools", "CalculatorTools", 
                    "ChartTools", "ReasoningTools", "KnowledgeTools"
                ],
                "tool_categories": {
                    "search": ["DuckDuckGoTools"],
                    "finance": ["YFinanceTools", "CalculatorTools"],
                    "visualization": ["ChartTools"],
                    "reasoning": ["ReasoningTools"],
                    "knowledge": ["KnowledgeTools"]
                },
                "tool_domains": {
                    "finance": ["YFinanceTools", "CalculatorTools", "ChartTools"],
                    "marketing": ["DuckDuckGoTools", "ChartTools"],
                    "legal": ["DuckDuckGoTools"],
                    "technology": ["DuckDuckGoTools", "ReasoningTools"]
                }
            }
        except Exception as e:
            logger.error(f"Error loading tools registry: {e}")
            return {"available_tools": [], "tool_categories": {}, "tool_domains": {}}
    
    def _load_domain_patterns(self) -> Dict[str, List[str]]:
        """Load domain-specific patterns for intelligent detection"""
        return {
            "finance": [
                r"\b(investir|investimento|ação|ações|fii|fii[s]?|cdb|tesouro|renda|fixa|variável)\b",
                r"\b(real|r\$|dólar|euro|moeda)\b",
                r"\b(mercado|bolsa|b3|cvm|anbima)\b",
                r"\b(risco|retorno|lucro|prejuízo|ganho|perda)\b",
                r"\b(portfólio|carteira|diversificação)\b"
            ],
            "marketing": [
                r"\b(marketing|publicidade|anúncio|campanha|seo|sem)\b",
                r"\b(redes sociais|instagram|facebook|linkedin|twitter)\b",
                r"\b(conversão|lead|cliente|venda|vendas)\b",
                r"\b(analytics|métricas|kpi|roi)\b"
            ],
            "legal": [
                r"\b(lei|legal|jurídico|processo|contrato|documento)\b",
                r"\b(advogado|advocacia|tribunal|justiça)\b",
                r"\b(compliance|regulamentação|norma|regulamento)\b"
            ],
            "technology": [
                r"\b(programação|código|software|desenvolvimento)\b",
                r"\b(api|backend|frontend|database|banco de dados)\b",
                r"\b(arquitetura|sistema|tecnologia|tech)\b"
            ]
        }
    
    def _load_context_classifier(self) -> Dict[str, Any]:
        """Load intelligent context classification model"""
        # This would ideally use a trained NLP model
        # For now, we'll use pattern-based classification with confidence scoring
        return {
            "market_indicators": {
                "brazilian": [
                    r"\b(real|r\$|b3|cvm|anbima|infomoney|xp)\b",
                    r"\b(mercado brasileiro|bolsa brasileira)\b",
                    r"\b(fii|fii[s]?|cdb|tesouro)\b",
                    r"\b(liberdade financeira|investir com segurança)\b"
                ],
                "american": [
                    r"\b(dollar|\$|nyse|nasdaq|sec|morningstar)\b",
                    r"\b(us market|american market)\b"
                ],
                "european": [
                    r"\b(euro|€|euronext|lse|fca)\b",
                    r"\b(european market|eu market)\b"
                ]
            },
            "complexity_indicators": {
                "simple": [
                    r"\b(simples|básico|fácil|direto)\b",
                    r"\b(resumo|overview|visão geral)\b"
                ],
                "complex": [
                    r"\b(complexo|detalhado|análise profunda|estudo completo)\b",
                    r"\b(análise técnica|fundamentalista|quantitativa)\b"
                ]
            }
        }
    
    def classify_context_intelligently(self, user_input: str) -> Dict[str, Any]:
        """Intelligently classify user context using pattern matching and confidence scoring"""
        context = {
            "detected_domains": [],
            "market_context": None,
            "complexity_level": "medium",
            "confidence_scores": {}
        }
        
        user_input_lower = user_input.lower()
        
        # Detect domains with confidence scoring
        for domain, patterns in self.domain_patterns.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, user_input_lower, re.IGNORECASE):
                    matches += 1
            
            confidence = min(matches / len(patterns), 1.0)
            if confidence > 0.3:  # Threshold for domain detection
                context["detected_domains"].append({
                    "domain": domain,
                    "confidence": confidence
                })
        
        # Detect market context
        for market, patterns in self.context_classifier["market_indicators"].items():
            matches = sum(1 for pattern in patterns if re.search(pattern, user_input_lower, re.IGNORECASE))
            if matches > 0:
                context["market_context"] = {
                    "market": market,
                    "confidence": min(matches / len(patterns), 1.0)
                }
                break
        
        # Detect complexity level
        for level, patterns in self.context_classifier["complexity_indicators"].items():
            matches = sum(1 for pattern in patterns if re.search(pattern, user_input_lower, re.IGNORECASE))
            if matches > 0:
                context["complexity_level"] = level
                break
        
        return context
    
    def validate_tools_intelligently(self, tools_config: List[Dict], context: Dict[str, Any]) -> List[ValidationIssue]:
        """Intelligently validate tool configuration based on context"""
        issues = []
        recommended_tools = [tool.get("name") for tool in tools_config if tool.get("enabled", False)]
        
        # Check for non-existent tools
        for tool_name in recommended_tools:
            if tool_name not in self.tools_registry["available_tools"]:
                issues.append(ValidationIssue(
                    level=ValidationLevel.CRITICAL,
                    category="tool_validation",
                    message=f"Ferramenta inexistente: {tool_name}",
                    suggestion=f"Substituir {tool_name} por ferramenta disponível no Agno",
                    confidence=1.0,
                    context={"tool_name": tool_name}
                ))
        
        # Check for missing essential tools based on domain
        for domain_info in context.get("detected_domains", []):
            domain = domain_info["domain"]
            confidence = domain_info["confidence"]
            
            if domain in self.tools_registry["tool_domains"]:
                expected_tools = self.tools_registry["tool_domains"][domain]
                missing_tools = [tool for tool in expected_tools if tool not in recommended_tools]
                
                for tool in missing_tools:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="tool_recommendation",
                        message=f"Ferramenta essencial ausente para {domain}: {tool}",
                        suggestion=f"Adicionar {tool} para melhor funcionalidade em {domain}",
                        confidence=confidence,
                        context={"domain": domain, "tool": tool}
                    ))
        
        # Check for market context appropriateness
        market_context = context.get("market_context")
        if market_context and market_context["market"] == "brazilian":
            american_tools = ["MintAPI", "PlaidAPI"]  # These would be detected as non-existent anyway
            for tool in american_tools:
                if tool in recommended_tools:
                    issues.append(ValidationIssue(
                        level=ValidationLevel.WARNING,
                        category="market_context",
                        message=f"Ferramenta americana para contexto brasileiro: {tool}",
                        suggestion="Considerar ferramentas apropriadas para mercado brasileiro",
                        confidence=market_context["confidence"],
                        context={"market": "brazilian", "tool": tool}
                    ))
        
        return issues
    
    def validate_knowledge_base_intelligently(self, knowledge_config: Dict, context: Dict[str, Any]) -> List[ValidationIssue]:
        """Intelligently validate knowledge base configuration"""
        issues = []
        
        if not knowledge_config.get("enabled", False):
            return issues
        
        sources = knowledge_config.get("sources", [])
        
        # Check for generic/placeholder sources
        generic_patterns = [
            r"exemplo_url", r"placeholder", r"generic", r"template",
            r"url\d+", r"source\d+", r"example\d+"
        ]
        
        for source in sources:
            source_str = str(source).lower()
            for pattern in generic_patterns:
                if re.search(pattern, source_str):
                    issues.append(ValidationIssue(
                        level=ValidationLevel.CRITICAL,
                        category="knowledge_quality",
                        message=f"Fonte genérica detectada: {source}",
                        suggestion="Substituir por fontes específicas e relevantes",
                        confidence=0.9,
                        context={"source": source, "pattern": pattern}
                    ))
                    break
        
        # Check for market context appropriateness
        market_context = context.get("market_context")
        if market_context and market_context["market"] == "brazilian":
            american_sources = [
                r"morningstar\.com", r"yahoo\.com", r"bloomberg\.com",
                r"marketwatch\.com", r"cnbc\.com"
            ]
            
            for source in sources:
                source_str = str(source).lower()
                for pattern in american_sources:
                    if re.search(pattern, source_str):
                        issues.append(ValidationIssue(
                            level=ValidationLevel.WARNING,
                            category="market_context",
                            message=f"Fonte americana para contexto brasileiro: {source}",
                            suggestion="Considerar fontes brasileiras como Infomoney, XP Research, B3",
                            confidence=market_context["confidence"],
                            context={"market": "brazilian", "source": source}
                        ))
                        break
        
        return issues
    
    def validate_context_preservation_intelligently(self, user_input: str, specification: Dict) -> List[ValidationIssue]:
        """Intelligently validate if user context is preserved in specification"""
        issues = []
        
        # Extract key concepts from user input using NLP-like approach
        user_concepts = self._extract_key_concepts(user_input)
        spec_content = json.dumps(specification, ensure_ascii=False).lower()
        
        # Check for concept preservation with confidence scoring
        for concept, importance in user_concepts.items():
            if concept.lower() not in spec_content:
                issues.append(ValidationIssue(
                    level=ValidationLevel.WARNING,
                    category="context_preservation",
                    message=f"Conceito importante não refletido: {concept}",
                    suggestion=f"Incluir '{concept}' na especificação",
                    confidence=importance,
                    context={"concept": concept, "importance": importance}
                ))
        
        return issues
    
    def _extract_key_concepts(self, user_input: str) -> Dict[str, float]:
        """Extract key concepts from user input with importance scoring"""
        concepts = {}
        
        # Define concept patterns with importance weights
        concept_patterns = {
            "gastos pessoais": 0.9,
            "furos nos gastos": 0.8,
            "investir": 0.9,
            "liberdade financeira": 0.8,
            "visão de mercado": 0.7,
            "investir com segurança": 0.8,
            "bom retorno": 0.7,
            "FIIs": 0.8,
            "cálculos": 0.6,
            "análise": 0.7,
            "rendimento": 0.6,
            "opções": 0.5,
            "mercado brasileiro": 0.8,
            "real": 0.7,
            "r\$": 0.7,
            "baixo risco": 0.8,
            "alto risco": 0.8
        }
        
        user_input_lower = user_input.lower()
        
        for concept, importance in concept_patterns.items():
            if concept.lower() in user_input_lower:
                concepts[concept] = importance
        
        return concepts
    
    def validate_specification_intelligently(self, user_input: str, specification: Dict, domain: str = None, use_case: str = None) -> Dict[str, Any]:
        """Comprehensive intelligent validation of agent specification"""
        
        # Classify context intelligently
        context = self.classify_context_intelligently(user_input)
        
        # Collect all validation issues
        all_issues = []
        
        # Validate tools intelligently
        tools_config = specification.get("tools_config", [])
        tool_issues = self.validate_tools_intelligently(tools_config, context)
        all_issues.extend(tool_issues)
        
        # Validate knowledge base intelligently
        knowledge_config = specification.get("knowledge_base", {})
        knowledge_issues = self.validate_knowledge_base_intelligently(knowledge_config, context)
        all_issues.extend(knowledge_issues)
        
        # Validate context preservation intelligently
        context_issues = self.validate_context_preservation_intelligently(user_input, specification)
        all_issues.extend(context_issues)
        
        # Calculate intelligent score
        score = self._calculate_intelligent_score(all_issues, context)
        
        # Generate intelligent suggestions
        suggestions = self._generate_intelligent_suggestions(all_issues, context)
        
        # Store validation for learning
        self._store_validation_for_learning(user_input, specification, all_issues, score)
        
        return {
            "is_valid": score >= 70,
            "score": score,
            "issues": [self._issue_to_dict(issue) for issue in all_issues],
            "suggestions": suggestions,
            "context_analysis": context,
            "confidence_metrics": self._calculate_confidence_metrics(all_issues)
        }
    
    def _calculate_intelligent_score(self, issues: List[ValidationIssue], context: Dict[str, Any]) -> float:
        """Calculate intelligent validation score based on issues and context"""
        base_score = 100.0
        
        # Weight issues by level and confidence
        for issue in issues:
            if issue.level == ValidationLevel.CRITICAL:
                base_score -= 20 * issue.confidence
            elif issue.level == ValidationLevel.WARNING:
                base_score -= 10 * issue.confidence
            elif issue.level == ValidationLevel.INFO:
                base_score -= 5 * issue.confidence
        
        # Adjust score based on context complexity
        complexity = context.get("complexity_level", "medium")
        if complexity == "complex":
            base_score += 5  # Bonus for complex requirements
        elif complexity == "simple":
            base_score -= 5  # Penalty for oversimplification
        
        return max(0.0, min(100.0, base_score))
    
    def _generate_intelligent_suggestions(self, issues: List[ValidationIssue], context: Dict[str, Any]) -> List[str]:
        """Generate intelligent improvement suggestions"""
        suggestions = []
        
        # Group issues by category for better suggestions
        issues_by_category = {}
        for issue in issues:
            if issue.category not in issues_by_category:
                issues_by_category[issue.category] = []
            issues_by_category[issue.category].append(issue)
        
        # Generate contextual suggestions
        for category, category_issues in issues_by_category.items():
            if category == "tool_validation":
                suggestions.append("🔧 **Ferramentas:** Substituir ferramentas inexistentes por opções disponíveis no Agno")
            elif category == "tool_recommendation":
                suggestions.append("📊 **Funcionalidade:** Adicionar ferramentas essenciais para melhor performance")
            elif category == "market_context":
                suggestions.append("🌍 **Contexto:** Adaptar ferramentas e fontes para o mercado local")
            elif category == "knowledge_quality":
                suggestions.append("📚 **Conhecimento:** Usar fontes específicas e relevantes")
            elif category == "context_preservation":
                suggestions.append("🎯 **Contexto:** Incorporar todos os requisitos do usuário na especificação")
        
        return suggestions
    
    def _calculate_confidence_metrics(self, issues: List[ValidationIssue]) -> Dict[str, float]:
        """Calculate confidence metrics for validation results"""
        if not issues:
            return {"overall_confidence": 1.0}
        
        avg_confidence = sum(issue.confidence for issue in issues) / len(issues)
        critical_issues = [issue for issue in issues if issue.level == ValidationLevel.CRITICAL]
        
        return {
            "overall_confidence": avg_confidence,
            "critical_issues_count": len(critical_issues),
            "validation_coverage": min(len(issues) / 10, 1.0)  # Normalize coverage
        }
    
    def _issue_to_dict(self, issue: ValidationIssue) -> Dict[str, Any]:
        """Convert ValidationIssue to dictionary"""
        return {
            "level": issue.level.value,
            "category": issue.category,
            "message": issue.message,
            "suggestion": issue.suggestion,
            "confidence": issue.confidence,
            "context": issue.context
        }
    
    def _store_validation_for_learning(self, user_input: str, specification: Dict, issues: List[ValidationIssue], score: float):
        """Store validation data for future learning"""
        validation_record = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "specification": specification,
            "issues": [self._issue_to_dict(issue) for issue in issues],
            "score": score
        }
        
        self.validation_history.append(validation_record)
        
        # Keep only last 1000 validations for memory management
        if len(self.validation_history) > 1000:
            self.validation_history = self.validation_history[-1000:]
    
    def learn_from_feedback(self, validation_id: str, user_feedback: Dict[str, Any]):
        """Learn from user feedback to improve validation rules"""
        # This would implement learning algorithms
        # For now, we'll store feedback for future implementation
        logger.info(f"Learning from feedback: {validation_id} - {user_feedback}")


# Global intelligent validator instance
intelligent_validator = IntelligentValidator()
