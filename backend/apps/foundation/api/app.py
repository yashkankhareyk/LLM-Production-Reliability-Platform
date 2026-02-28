import os
from fastapi import FastAPI, Depends
from dotenv import load_dotenv
from shared.schemas.chat import ChatRequest, ChatResponse
from apps.foundation.core.llm_service import LLMService
from apps.foundation.providers.grok_adapter import GrokProvider
from apps.foundation.providers.openrouter_adapter import OpenRouterProvider

load_dotenv()


def create_llm_service() -> LLMService:
    providers = []

    grok_key = os.getenv("GROK_API_KEY")
    if grok_key:
        providers.append(
            GrokProvider(
                api_key=grok_key,
                base_url=os.getenv(
                    "GROK_BASE_URL", "https://api.x.ai/v1"
                ),
            )
        )

    or_key = os.getenv("OPENROUTER_API_KEY")
    if or_key:
        providers.append(
            OpenRouterProvider(
                api_key=or_key,
                base_url=os.getenv(
                    "OPENROUTER_BASE_URL",
                    "https://openrouter.ai/api/v1",
                ),
            )
        )

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
    async def llm_chat(request: ChatRequest):
        return await llm_service.chat(request)

    return app