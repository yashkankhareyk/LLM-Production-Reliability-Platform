import os
# from fastapi import FastAPI, Depends
from fastapi import FastAPI, Header
from typing import Optional
from dotenv import load_dotenv
from shared.schemas.chat import ChatRequest, ChatResponse
from apps.foundation.core.llm_service import LLMService
from apps.foundation.providers.grok_adapter import GrokProvider
from apps.foundation.providers.openrouter_adapter import OpenRouterProvider
from apps.foundation.providers.mock_adapter import MockProvider

load_dotenv()


def create_llm_service() -> LLMService:
    providers = []

    grok_key = os.getenv("GROK_API_KEY")
    grok_enabled = os.getenv("GROK_ENABLED", "false").lower() == "true"
    if grok_key:
        providers.append(
            GrokProvider(
                api_key=grok_key,
                base_url=os.getenv(
                    "GROK_BASE_URL", "https://api.x.ai/v1"
                ),
            )
        )

    # OpenRouter
    or_key = os.getenv("OPENROUTER_API_KEY")
    if or_key and or_key != "your-openrouter-key":
        providers.append(
            OpenRouterProvider(
                api_key=or_key,
                base_url=os.getenv(
                    "OPENROUTER_BASE_URL",
                    "https://openrouter.ai/api/v1",
                ),
            )
        )
    # Always add mock as last fallback
    providers.append(MockProvider())
    return LLMService(providers=providers)


def create_app() -> FastAPI:
    app = FastAPI(title="Layer 1: Foundation", version="0.1.0")
    llm_service = create_llm_service()

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "layer": "foundation",
            "providers": [p.name for p in llm_service.providers],
        }

    @app.post("/internal/llm/chat", response_model=ChatResponse)
    async def llm_chat(
        request: ChatRequest,
        x_client_id: Optional[str] = Header(
            default="default"
        ),
    ):
        return await llm_service.chat(
            request, client_id=x_client_id
        )
    
    @app.get("/internal/guardrails/status")
    async def guardrails_status():
        """View guardrail configuration and rate limit status."""
        from apps.foundation.guardrails.rate_limiter import (
            rate_limiter,
            REQUESTS_PER_MINUTE,
            REQUESTS_PER_HOUR,
            TOKEN_BUDGET_PER_HOUR,
        )

        return {
            "guardrails_enabled": True,
            "checks": [
                "input_validator",
                "content_filter",
                "prompt_injection",
                "pii_detector",
                "rate_limiter",
                "output_validator",
            ],
            "rate_limits": {
                "requests_per_minute": REQUESTS_PER_MINUTE,
                "requests_per_hour": REQUESTS_PER_HOUR,
                "token_budget_per_hour": TOKEN_BUDGET_PER_HOUR,
            },
            "pii_mode": "warn",
        }

    return app