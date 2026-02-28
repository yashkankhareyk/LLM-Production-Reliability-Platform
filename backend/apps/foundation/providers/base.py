# Provider adapter interface (single responsibility)
"""Base provider adapter — every LLM provider implements this."""
from abc import ABC, abstractmethod
from shared.schemas.chat import ChatRequest, ChatResponse


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def chat(self, request: ChatRequest) -> ChatResponse:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass