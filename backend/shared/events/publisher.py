"""Convenience helper for publishing events."""
from shared.schemas.events import EventEnvelope
from shared.events.event_bus import InMemoryEventBus


async def emit_event(
    event_type: str,
    correlation_id: str,
    layer: str,
    payload: dict = None,
):
    """
    Simple helper to emit an event from anywhere.

    Usage:
        await emit_event(
            "llm.request.started",
            correlation_id="abc-123",
            layer="foundation",
            payload={"provider": "grok"}
        )
    """
    bus = InMemoryEventBus()
    event = EventEnvelope(
        event_type=event_type,
        correlation_id=correlation_id,
        layer=layer,
        payload=payload or {},
    )
    await bus.publish(event)