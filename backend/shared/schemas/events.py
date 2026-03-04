# Pydantic: EventEnvelope + event payloads
"""Event schemas — the contract for all events across layers."""
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid


class EventEnvelope(BaseModel):
    event_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )
    correlation_id: str
    event_type: str
    timestamp: datetime = Field(
        default_factory=datetime.utcnow
    )
    layer: str
    payload: Dict[str, Any] = {}


class RunSummary(BaseModel):
    correlation_id: str
    started_at: str
    events: List[Dict[str, Any]]
    total_events: int
    status: str  # "completed", "failed", "in_progress"
    total_latency_ms: float = 0.0
    providers_used: List[str] = []
    search_layers_used: List[str] = []