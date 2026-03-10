import time
import httpx
import logging
from shared.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
)
from apps.foundation.providers.base import LLMProvider

logger = logging.getLogger(__name__)


class GrokProvider(LLMProvider):
    name = "grok"

    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = "grok-3-mini-latest"  # ← Changed model

    async def chat(self, request: ChatRequest) -> ChatResponse:
        start = time.time()

        # Filter messages to only valid roles
        valid_roles = {"user", "assistant", "system"}
        messages = []
        for m in request.messages:
            role = m.role if m.role in valid_roles else "user"
            messages.append(
                {"role": role, "content": m.content}
            )

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )

            # Log the error details before raising
            if resp.status_code != 200:
                logger.error(
                    f"Grok API error {resp.status_code}: "
                    f"{resp.text}"
                )
                resp.raise_for_status()

            data = resp.json()

        latency = (time.time() - start) * 1000
        choice = data["choices"][0]["message"]
        usage = data.get("usage", {})

        return ChatResponse(
            message=ChatMessage(
                role=choice["role"],
                content=choice["content"],
            ),
            provider="grok",
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
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    },
                )
                return resp.status_code == 200
        except Exception:
            return False