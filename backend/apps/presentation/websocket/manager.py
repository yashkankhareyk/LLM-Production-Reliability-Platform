"""WebSocket connection manager — handles multiple clients."""
import json
import logging
import asyncio
from typing import Set
from fastapi import WebSocket
from shared.schemas.events import EventEnvelope

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections and broadcasts events."""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(
            f"🔌 WebSocket connected. "
            f"Active: {len(self.active_connections)}"
        )

        # Send welcome message
        await websocket.send_json(
            {
                "type": "connection",
                "message": "Connected to live event stream",
                "active_connections": len(
                    self.active_connections
                ),
            }
        )

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        logger.info(
            f"🔌 WebSocket disconnected. "
            f"Active: {len(self.active_connections)}"
        )

    async def broadcast_event(self, event: EventEnvelope):
        """Send event to all connected clients."""
        if not self.active_connections:
            return

        data = {
            "type": "event",
            "event_id": event.event_id,
            "correlation_id": event.correlation_id,
            "event_type": event.event_type,
            "timestamp": event.timestamp.isoformat(),
            "layer": event.layer,
            "payload": event.payload,
        }

        message = json.dumps(data)
        disconnected = set()

        for websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.add(websocket)

        for ws in disconnected:
            self.active_connections.discard(ws)

    @property
    def connection_count(self) -> int:
        return len(self.active_connections)


# Global singleton
ws_manager = ConnectionManager()