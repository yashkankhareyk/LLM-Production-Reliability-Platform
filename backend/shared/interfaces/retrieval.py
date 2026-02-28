# Contract: retrieval interface
"""Retrieval contract — any search strategy must implement this."""
from abc import ABC, abstractmethod
from typing import List
from shared.schemas.chat import RetrievalSource


class RetrievalStrategy(ABC):
    """Base interface for all retrieval strategies."""

    @abstractmethod
    async def search(
        self, query: str, top_k: int = 3
    ) -> List[RetrievalSource]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass