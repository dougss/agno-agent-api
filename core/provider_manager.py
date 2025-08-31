from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
import logging
from enum import Enum

from agno.models.openai import OpenAIChat

# Conditional imports for optional providers
try:
    from agno.models.anthropic import Claude
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    Claude = None

try:
    from agno.models.google import Gemini
    GOOGLE_AVAILABLE = True
except ImportError:
    GOOGLE_AVAILABLE = False
    Gemini = None

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    """Supported LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class BaseProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    def create_model(self, model_id: str, **kwargs) -> Any:
        """Create model instance"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        pass
    
    @abstractmethod
    def validate_model_id(self, model_id: str) -> bool:
        """Validate if model_id is supported"""
        pass


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation"""
    
    def create_model(self, model_id: str, **kwargs) -> OpenAIChat:
        """Create OpenAI model instance"""
        return OpenAIChat(
            id=model_id,
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=kwargs.get("temperature", 0.7)
        )
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available OpenAI models"""
        return [
            {
                "id": "gpt-4o",
                "name": "GPT-4o",
                "description": "Most capable model for complex reasoning",
                "max_tokens": 4096,
                "recommended_for": ["complex_analysis", "creative_tasks", "reasoning"]
            },
            {
                "id": "gpt-4o-mini",
                "name": "GPT-4o Mini",
                "description": "Fast and efficient for most tasks",
                "max_tokens": 2000,
                "recommended_for": ["general_tasks", "specialized_agents", "cost_optimization"]
            },
            {
                "id": "gpt-3.5-turbo",
                "name": "GPT-3.5 Turbo",
                "description": "Fast and cost-effective for simple tasks",
                "max_tokens": 1000,
                "recommended_for": ["simple_tasks", "basic_support", "cost_sensitive"]
            }
        ]
    
    def validate_model_id(self, model_id: str) -> bool:
        """Validate OpenAI model ID"""
        valid_models = ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo"]
        return model_id in valid_models


class AnthropicProvider(BaseProvider):
    """Anthropic provider implementation"""
    
    def create_model(self, model_id: str, **kwargs) -> Claude:
        """Create Anthropic model instance"""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic provider not available. Please install anthropic package.")
        return Claude(
            id=model_id,
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=kwargs.get("temperature", 0.7)
        )
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available Anthropic models"""
        return [
            {
                "id": "claude-3-5-sonnet-20241022",
                "name": "Claude 3.5 Sonnet",
                "description": "Most capable Claude model for complex tasks",
                "max_tokens": 4096,
                "recommended_for": ["complex_analysis", "creative_tasks", "reasoning"]
            },
            {
                "id": "claude-3-haiku-20240307",
                "name": "Claude 3 Haiku",
                "description": "Fast and efficient for most tasks",
                "max_tokens": 2000,
                "recommended_for": ["general_tasks", "specialized_agents", "cost_optimization"]
            },
            {
                "id": "claude-3-opus-20240229",
                "name": "Claude 3 Opus",
                "description": "Most powerful model for advanced reasoning",
                "max_tokens": 4096,
                "recommended_for": ["advanced_reasoning", "research", "complex_problem_solving"]
            }
        ]
    
    def validate_model_id(self, model_id: str) -> bool:
        """Validate Anthropic model ID"""
        valid_models = [
            "claude-3-5-sonnet-20241022",
            "claude-3-haiku-20240307", 
            "claude-3-opus-20240229"
        ]
        return model_id in valid_models


class GoogleProvider(BaseProvider):
    """Google provider implementation"""
    
    def create_model(self, model_id: str, **kwargs) -> Gemini:
        """Create Google model instance"""
        if not GOOGLE_AVAILABLE:
            raise ImportError("Google provider not available. Please install google-generativeai package.")
        return Gemini(
            id=model_id,
            max_tokens=kwargs.get("max_tokens", 2000),
            temperature=kwargs.get("temperature", 0.7)
        )
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """Get available Google models"""
        return [
            {
                "id": "gemini-1.5-pro",
                "name": "Gemini 1.5 Pro",
                "description": "Most capable Gemini model",
                "max_tokens": 4096,
                "recommended_for": ["complex_analysis", "multimodal_tasks", "reasoning"]
            },
            {
                "id": "gemini-1.5-flash",
                "name": "Gemini 1.5 Flash",
                "description": "Fast and efficient Gemini model",
                "max_tokens": 2000,
                "recommended_for": ["general_tasks", "quick_responses", "cost_optimization"]
            }
        ]
    
    def validate_model_id(self, model_id: str) -> bool:
        """Validate Google model ID"""
        valid_models = ["gemini-1.5-pro", "gemini-1.5-flash"]
        return model_id in valid_models


class ProviderManager:
    """Manager for multiple LLM providers"""
    
    def __init__(self):
        self.providers = {
            ProviderType.OPENAI: OpenAIProvider(),
        }
        
        # Add optional providers if available
        if ANTHROPIC_AVAILABLE:
            self.providers[ProviderType.ANTHROPIC] = AnthropicProvider()
        
        if GOOGLE_AVAILABLE:
            self.providers[ProviderType.GOOGLE] = GoogleProvider()
    
    def get_provider(self, provider_type: str) -> Optional[BaseProvider]:
        """Get provider instance by type"""
        try:
            provider_enum = ProviderType(provider_type.lower())
            return self.providers.get(provider_enum)
        except ValueError:
            logger.warning(f"Unknown provider type: {provider_type}")
            return None
    
    def create_model(self, provider_type: str, model_id: str, **kwargs) -> Optional[Any]:
        """Create model instance from provider"""
        provider = self.get_provider(provider_type)
        if not provider:
            return None
        
        if not provider.validate_model_id(model_id):
            logger.error(f"Invalid model_id {model_id} for provider {provider_type}")
            return None
        
        try:
            return provider.create_model(model_id, **kwargs)
        except Exception as e:
            logger.error(f"Error creating model {model_id} from {provider_type}: {e}")
            return None
    
    def get_all_models(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all available models from all providers"""
        all_models = {}
        for provider_type, provider in self.providers.items():
            all_models[provider_type.value] = provider.get_available_models()
        return all_models
    
    def get_recommended_model(self, use_case: str) -> Dict[str, Any]:
        """Get recommended model for specific use case"""
        recommendations = {
            "complex_analysis": {
                "provider": "anthropic",
                "model_id": "claude-3-5-sonnet-20241022",
                "reason": "Best reasoning capabilities"
            },
            "cost_optimization": {
                "provider": "openai", 
                "model_id": "gpt-4o-mini",
                "reason": "Best cost-performance ratio"
            },
            "general_tasks": {
                "provider": "anthropic",
                "model_id": "claude-3-haiku-20240307", 
                "reason": "Fast and reliable for most tasks"
            },
            "creative_tasks": {
                "provider": "openai",
                "model_id": "gpt-4o",
                "reason": "Excellent creative capabilities"
            }
        }
        
        return recommendations.get(use_case, recommendations["general_tasks"])


# Global provider manager instance
provider_manager = ProviderManager()
