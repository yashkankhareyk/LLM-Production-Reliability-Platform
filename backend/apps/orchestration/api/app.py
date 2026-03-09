"""Layer 2: Orchestration — LangGraph agent API."""
import os
import uuid
import httpx
import logging
from fastapi import FastAPI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from shared.schemas.chat import ChatRequest, ChatResponse
from apps.orchestration.core.graph import RAGAgent
from apps.intelligence.retrieval.vector_store import (
    VectorStoreRetrieval,
)
from apps.intelligence.retrieval.local_search import (
    LocalFileRetrieval,
)
from apps.intelligence.retrieval.s3_search import S3Retrieval

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FOUNDATION_URL = os.getenv(
    "FOUNDATION_URL", "http://localhost:8001"
)


async def call_foundation_llm(
    request: ChatRequest,
) -> ChatResponse:
    """Forward LLM call to Layer 1."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{FOUNDATION_URL}/internal/llm/chat",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return ChatResponse(**resp.json())


def create_app() -> FastAPI:
    app = FastAPI(
        title="Layer 2: Orchestration",
        version="0.4.0",
        description="LangGraph RAG Agent — vector → local → S3 → LLM",
    )

    # Initialize retrievers (same data as Layer 3)
    vector_store = VectorStoreRetrieval(
        store_path=os.getenv(
            "VECTOR_STORE_PATH", "./data/vector_store"
        )
    )
    local_search = LocalFileRetrieval(
        docs_dir=os.getenv(
            "LOCAL_DOCS_PATH", "./data/local_docs"
        )
    )
    s3_search = S3Retrieval(
        bucket_path=os.getenv(
            "S3_MOCK_PATH", "./data/s3_mock"
        )
    )

    # Initialize LangGraph agent
    agent = RAGAgent(
        vector_retriever=vector_store,
        local_retriever=local_search,
        s3_retriever=s3_search,
        llm_chat_fn=call_foundation_llm,
    )

    # ─── HEALTH ─────────────────────────────────────

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "layer": "orchestration",
            "agent": "langgraph_rag",
            "vector_docs": len(vector_store.documents),
        }

    # ─── RUN AGENT ──────────────────────────────────

    class AgentRequest(BaseModel):
        query: str
        correlation_id: str = Field(
            default_factory=lambda: str(uuid.uuid4())
        )
        max_tokens: int = 512
        temperature: float = 0.7

    @app.post(
        "/internal/agent/run",
        summary="Run LangGraph RAG agent",
        description=(
            "Executes: vector_search → evaluate → "
            "local_search → evaluate → s3_search → "
            "select_sources → generate. "
            "Returns answer + sources + step details."
        ),
    )
    async def run_agent(req: AgentRequest):
        result = await agent.run(
            query=req.query,
            correlation_id=req.correlation_id,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
        )
        return result

    # ─── GRAPH INFO ─────────────────────────────────

    @app.get(
        "/internal/agent/graph",
        summary="View agent workflow graph structure",
    )
    async def get_graph():
        return agent.get_graph_info()

    return app