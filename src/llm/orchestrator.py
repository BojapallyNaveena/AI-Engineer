import logging
from typing import Dict, Any, List, Optional, Tuple
from .base_provider import BaseLLMProvider
from .gemini_provider import GeminiProvider
from .groq_provider import GroqProvider
from .deepseek_provider import DeepSeekProvider

logger = logging.getLogger(__name__)


class LLMOrchestrator:
    """
    LLM Orchestrator executing structured entity extraction with automatic fallback chain:
    Gemini (Primary) -> Groq (Fallback 1) -> DeepSeek (Fallback 2).
    """

    def __init__(self, providers: Optional[List[BaseLLMProvider]] = None):
        if providers is not None:
            self.providers = providers
        else:
            self.providers = [
                GeminiProvider(),
                GroqProvider(),
                DeepSeekProvider(),
            ]

    async def extract_entity_json(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
    ) -> Tuple[Dict[str, Any], str]:
        """
        Execute extraction prompt across configured providers in fallback order.
        
        Returns:
            Tuple[Dict[str, Any], str]: (parsed_json_result, successful_provider_name)
        """
        errors = []

        for provider in self.providers:
            if not provider.is_available:
                logger.info(f"LLM provider '{provider.name}' skipped (API key not configured).")
                continue

            logger.info(f"LLM provider selected: '{provider.name}'")
            try:
                result_json = await provider.extract_json(prompt, system_instruction=system_instruction)
                logger.info(f"Extraction successful using provider: '{provider.name}'")
                return result_json, provider.name
            except Exception as e:
                error_msg = f"LLM provider '{provider.name}' failed: {e}"
                logger.warning(error_msg)
                logger.info("Fallback provider selected...")
                errors.append(error_msg)

        all_err_str = "; ".join(errors) if errors else "No LLM providers available or configured."
        logger.error(f"All LLM extraction providers failed: {all_err_str}")
        raise RuntimeError(f"LLM Extraction failed across all providers: {all_err_str}")
