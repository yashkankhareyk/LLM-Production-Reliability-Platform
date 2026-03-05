# Contract: publish/subscribe interface
"""Event bus contract — publish/subscribe interface."""
from abc import ABC, abstractmethod
from typing import Callable, List
from shared.schemas.events import EventEnvelope


class EventPublisher(ABC):
    @abstractmethod
    async def publish(self, event: EventEnvelope) -> None:
        pass


class EventSubscriber(ABC):
    @abstractmethod
    async def subscribe(
        self,
        callback: Callable,
        event_types: List[str] = None,
    ) -> None:
        pass