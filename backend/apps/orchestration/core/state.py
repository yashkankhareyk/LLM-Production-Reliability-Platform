# Persists workflow state (in-memory/Redis/Postgres)
"""LangGraph state definition — flows through every node."""
from typing import TypedDict, List, Optional
from shared.schemas.chat import RetrievalSource


class RAGState(TypedDict):
    # Input
    query: str
    correlation_id: str
    max_tokens: int
    temperature: float

    # Search results from each strategy
    vector_results: List[RetrievalSource]
    local_results: List[RetrievalSource]
    s3_results: List[RetrievalSource]

    # Selected best sources
    best_sources: List[RetrievalSource]

    # Tracking
    search_path: List[str]
    current_step: str
    step_details: List[dict]

    # Output
    answer: str
    provider: str
    model: str
    tokens_used: int
    total_latency_ms: float
    error: Optional[str]