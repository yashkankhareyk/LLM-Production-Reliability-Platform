# Main use-case: validate → route → call → fallback
"""Core LLM service — routing + fallback logic."""
import logging
from typing import List
from shared.schemas.chat import ChatRequest, ChatResponse, ChatMessage
from apps.foundation.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class LLMService:
    """
    Tries providers in order. If one fails, falls back to the next.
    """

    def __init__(self, providers: List[LLMProvider]):
        self.providers = providers

    async def chat(self, request: ChatRequest) -> ChatResponse:
        errors = []

        for provider in self.providers:
            try:
                logger.info(
                    f"Trying provider: {provider.name} "
                    f"| correlation_id={request.correlation_id}"
                )
                response = await provider.chat(request)
                logger.info(
                    f"Success: {provider.name} "
                    f"| {response.tokens_used} tokens "
                    f"| {response.latency_ms}ms"
                )
                return response

            except Exception as e:
                logger.warning(
                    f"Provider {provider.name} failed: {e}"
                )
                errors.append(f"{provider.name}: {str(e)}")
                continue

        # All providers failed
        error_summary = " | ".join(errors)
        logger.error(f"All providers failed: {error_summary}")

        return ChatResponse(
            message=ChatMessage(
                role="assistant",
                content=(
                    "I'm sorry, all LLM providers are currently "
                    "unavailable. Please try again later."
                ),
            ),
            provider="none",
            model="fallback",
            tokens_used=0,
            latency_ms=0,
            correlation_id=request.correlation_id,
        )