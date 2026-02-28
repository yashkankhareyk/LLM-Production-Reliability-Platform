# Pydantic: ChatRequest/ChatResponse
"""Shared chat schemas — the contract between all layers."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid


class ChatMessage(BaseModel):
    role: str = Field(..., description="'user', 'assistant', or 'system'")
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    use_rag: bool = Field(default=False, description="Enable retrieval")
    max_tokens: int = 512
    temperature: float = 0.7
    correlation_id: str = Field(
        default_factory=lambda: str(uuid.uuid4())
    )


class RetrievalSource(BaseModel):
    content: str
    source_type: str  # "vector", "local", "s3"
    source_path: str
    score: float = 0.0


class ChatResponse(BaseModel):
    message: ChatMessage
    provider: str  # "grok", "openrouter"
    model: str
    sources: List[RetrievalSource] = []
    tokens_used: int = 0
    latency_ms: float = 0.0
    correlation_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)