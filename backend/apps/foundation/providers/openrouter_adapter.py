import time
import httpx
from shared.schemas.chat import (
    ChatRequest, ChatResponse, ChatMessage,
)
from apps.foundation.providers.base import LLMProvider


class OpenRouterProvider(LLMProvider):
    name = "openrouter"

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "meta-llama/llama-3-70b-instruct"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        start = time.time()

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": m.role, "content": m.content}
                        for m in request.messages
                    ],
                    "max_tokens": request.max_tokens,
                    "temperature": request.temperature,
                },
            )
            resp.raise_for_status()
            data = resp.json()

        latency = (time.time() - start) * 1000
        choice = data["choices"][0]["message"]
        usage = data.get("usage", {})

        return ChatResponse(
            message=ChatMessage(
                role=choice["role"], content=choice["content"]
            ),
            provider="openrouter",
            model=self.model,
            tokens_used=usage.get("total_tokens", 0),
            latency_ms=round(latency, 2),
            correlation_id=request.correlation_id,
        )

    async def health_check(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return resp.status_code == 200
        except Exception:
            return False