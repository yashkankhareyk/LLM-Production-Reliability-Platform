import asyncio
from shared.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
)
from apps.foundation.providers.base import LLMProvider


class MockProvider(LLMProvider):
    name = "mock"

    async def chat(self, request: ChatRequest) -> ChatResponse:
        await asyncio.sleep(0.3)
        user_msg = request.messages[-1].content

        # Build a simple response using the context if provided
        system_msgs = [
            m for m in request.messages if m.role == "system"
        ]
        if system_msgs:
            context = system_msgs[0].content
            content = (
                f"Based on the provided context, here is what I found "
                f"regarding your query '{user_msg}':\n\n"
                f"The context contains the following relevant information:\n"
                f"{context[context.find('CONTEXT:') + 8:context.find('CONTEXT:') + 500] if 'CONTEXT:' in context else context[:500]}"
            )
        else:
            content = f"[MOCK] You asked: '{user_msg}'. Configure real API keys for actual responses."

        return ChatResponse(
            message=ChatMessage(
                role="assistant",
                content=content,
            ),
            provider="mock",
            model="mock-v1",
            tokens_used=25,
            latency_ms=300,
            correlation_id=request.correlation_id,
        )

    async def health_check(self) -> bool:
        return True