# FastAPI app factory
import os
import httpx
from fastapi import FastAPI
from dotenv import load_dotenv

from shared.schemas.chat import ChatRequest, ChatResponse
from apps.intelligence.core.rag_service import RAGService
from apps.intelligence.retrieval.vector_store import VectorStoreRetrieval
from apps.intelligence.retrieval.local_search import LocalFileRetrieval
from apps.intelligence.retrieval.s3_search import S3Retrieval

load_dotenv()

FOUNDATION_URL = os.getenv("FOUNDATION_URL", "http://localhost:8001")


async def call_foundation_llm(request: ChatRequest) -> ChatResponse:
    """Forward to Layer 1 for LLM completion."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{FOUNDATION_URL}/internal/llm/chat",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return ChatResponse(**resp.json())


def create_app() -> FastAPI:
    app = FastAPI(title="Layer 3: Intelligence", version="0.2.0")

    # Initialize retrievers
    vector_store = VectorStoreRetrieval(
        store_path=os.getenv("VECTOR_STORE_PATH", "./data/vector_store")
    )
    local_search = LocalFileRetrieval(
        docs_dir=os.getenv("LOCAL_DOCS_PATH", "./data/local_docs")
    )
    s3_search = S3Retrieval(
        bucket_path=os.getenv("S3_MOCK_PATH", "./data/s3_mock")
    )

    rag_service = RAGService(
        vector_retriever=vector_store,
        local_retriever=local_search,
        s3_retriever=s3_search,
        llm_chat_fn=call_foundation_llm,
    )

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "layer": "intelligence",
            "vector_docs": len(vector_store.documents)
            if hasattr(vector_store, "documents")
            else 0,
        }

    @app.post("/internal/rag/answer", response_model=ChatResponse)
    async def rag_answer(request: ChatRequest):
        return await rag_service.answer(request)

    # === INGESTION ENDPOINTS ===
    from pydantic import BaseModel
    from typing import List

    class IngestRequest(BaseModel):
        texts: List[str]
        source_paths: List[str]

    @app.post("/internal/rag/ingest")
    async def ingest_documents(req: IngestRequest):
        vector_store.ingest(req.texts, req.source_paths)
        return {
            "status": "ingested",
            "count": len(req.texts),
            "total": len(vector_store.documents),
        }

    return app