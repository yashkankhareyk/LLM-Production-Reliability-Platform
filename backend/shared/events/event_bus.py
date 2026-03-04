"""
Event bus implementation.
- Starts with in-memory (works without Redis)
- Automatically uses Redis if available
"""
import json
import asyncio
import logging
from typing import List, Callable, Optional
from datetime import datetime

from shared.schemas.events import EventEnvelope
from shared.interfaces.event_bus import (
    EventPublisher,
    EventSubscriber,
)

logger = logging.getLogger(__name__)


class InMemoryEventBus(EventPublisher, EventSubscriber):
    """
    In-memory event bus.
    Works without any external dependencies.
    All services share this if running in same process.
    For cross-process: use Redis version below.
    """

    _instance = None
    _events: List[EventEnvelope] = []
    _subscribers: List[Callable] = []

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._events = []
            cls._subscribers = []
        return cls._instance

    async def publish(self, event: EventEnvelope) -> None:
        self._events.append(event)
        logger.info(
            f"📡 [{event.layer}] {event.event_type} "
            f"| cid={event.correlation_id[:8]}..."
        )

        for callback in self._subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.warning(f"Subscriber error: {e}")

    async def subscribe(
        self,
        callback: Callable,
        event_types: List[str] = None,
    ) -> None:
        if event_types:
            # Wrap callback to filter by event type
            original = callback

            async def filtered(event: EventEnvelope):
                if event.event_type in event_types:
                    if asyncio.iscoroutinefunction(original):
                        await original(event)
                    else:
                        original(event)

            self._subscribers.append(filtered)
        else:
            self._subscribers.append(callback)

    def get_events(
        self,
        correlation_id: str = None,
        event_type: str = None,
        layer: str = None,
        limit: int = 100,
    ) -> List[EventEnvelope]:
        events = self._events

        if correlation_id:
            events = [
                e
                for e in events
                if e.correlation_id == correlation_id
            ]
        if event_type:
            events = [
                e
                for e in events
                if e.event_type == event_type
            ]
        if layer:
            events = [
                e for e in events if e.layer == layer
            ]

        return events[-limit:]

    def get_runs(self, limit: int = 20) -> List[dict]:
        """Group events by correlation_id into runs."""
        runs = {}

        for event in self._events:
            cid = event.correlation_id
            if cid not in runs:
                runs[cid] = {
                    "correlation_id": cid,
                    "started_at": event.timestamp.isoformat(),
                    "events": [],
                    "status": "in_progress",
                    "providers_used": set(),
                    "search_layers_used": set(),
                }

            runs[cid]["events"].append(
                {
                    "type": event.event_type,
                    "layer": event.layer,
                    "time": event.timestamp.isoformat(),
                    "payload": event.payload,
                }
            )

            # Track metadata
            provider = event.payload.get("provider")
            if provider:
                runs[cid]["providers_used"].add(provider)

            search_layer = event.payload.get(
                "search_layer"
            )
            if search_layer:
                runs[cid]["search_layers_used"].add(
                    search_layer
                )

            # Detect status
            if "failed" in event.event_type:
                runs[cid]["status"] = "failed"
            elif "completed" in event.event_type:
                runs[cid]["status"] = "completed"

        # Convert sets to lists for JSON
        result = []
        for run in list(runs.values())[-limit:]:
            run["providers_used"] = list(
                run["providers_used"]
            )
            run["search_layers_used"] = list(
                run["search_layers_used"]
            )
            run["total_events"] = len(run["events"])
            result.append(run)

        return result

    def clear(self):
        self._events.clear()
        logger.info("Event store cleared")

    @property
    def total_events(self) -> int:
        return len(self._events)