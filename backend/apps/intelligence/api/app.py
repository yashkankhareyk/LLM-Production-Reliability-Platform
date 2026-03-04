import os
import httpx
import logging
from fastapi import FastAPI, UploadFile, File, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from dotenv import load_dotenv

from shared.schemas.chat import ChatRequest, ChatResponse
from shared.utils.file_parser import parse_file
from apps.intelligence.core.rag_service import RAGService
from apps.intelligence.retrieval.vector_store import VectorStoreRetrieval
from apps.intelligence.retrieval.local_search import LocalFileRetrieval
from apps.intelligence.retrieval.s3_search import S3Retrieval

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FOUNDATION_URL = os.getenv("FOUNDATION_URL", "http://localhost:8001")


async def call_foundation_llm(request: ChatRequest) -> ChatResponse:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{FOUNDATION_URL}/internal/llm/chat",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return ChatResponse(**resp.json())


def create_app() -> FastAPI:
    app = FastAPI(title="Layer 3: Intelligence", version="0.2.0")

    vector_store = VectorStoreRetrieval(
        store_path=os.getenv(
            "VECTOR_STORE_PATH", "./data/vector_store"
        )
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

    # ─── HEALTH ─────────────────────────────────────────

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "layer": "intelligence",
            "vector_docs": len(vector_store.documents),
            "vector_index_size": vector_store.index.ntotal
            if vector_store.index
            else 0,
        }

    # ─── RAG ANSWER ─────────────────────────────────────

    @app.post("/internal/rag/answer", response_model=ChatResponse)
    async def rag_answer(request: ChatRequest):
        return await rag_service.answer(request)

    # ─── FILE UPLOAD (CSV, PDF, TXT) ───────────────────

    @app.post("/internal/rag/ingest/file")
    async def ingest_file(file: UploadFile = File(...)):
        """
        Upload a file (CSV, PDF, TXT) → parse → chunk → embed → store.
        """
        allowed = {".csv", ".pdf", ".txt", ".md"}
        ext = ""
        if file.filename:
            ext = "." + file.filename.rsplit(".", 1)[-1].lower()

        if ext not in allowed:
            raise HTTPException(
                400,
                f"Unsupported file type: {ext}. "
                f"Allowed: {allowed}",
            )

        content = await file.read()

        if len(content) == 0:
            raise HTTPException(400, "File is empty")

        logger.info(
            f"Processing file: {file.filename} "
            f"({len(content)} bytes)"
        )

        texts, source_paths = parse_file(file.filename, content)

        if not texts:
            raise HTTPException(
                400,
                "Could not extract any text from file. "
                "Check file content.",
            )

        vector_store.ingest(texts, source_paths)

        return {
            "status": "success",
            "filename": file.filename,
            "file_size_bytes": len(content),
            "chunks_created": len(texts),
            "total_docs_in_store": len(vector_store.documents),
            "sample_chunks": [
                {
                    "source": source_paths[i],
                    "preview": texts[i][:200],
                }
                for i in range(min(3, len(texts)))
            ],
        }

    # ─── MULTIPLE FILES UPLOAD ──────────────────────────

    @app.post("/internal/rag/ingest/files")
    async def ingest_multiple_files(
        files: List[UploadFile] = File(...),
    ):
        """Upload multiple files at once."""
        results = []

        for file in files:
            try:
                content = await file.read()
                texts, source_paths = parse_file(
                    file.filename, content
                )

                if texts:
                    vector_store.ingest(texts, source_paths)
                    results.append(
                        {
                            "filename": file.filename,
                            "status": "success",
                            "chunks": len(texts),
                        }
                    )
                else:
                    results.append(
                        {
                            "filename": file.filename,
                            "status": "failed",
                            "error": "No text extracted",
                        }
                    )
            except Exception as e:
                results.append(
                    {
                        "filename": file.filename,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return {
            "total_files": len(files),
            "results": results,
            "total_docs_in_store": len(vector_store.documents),
        }

    # ─── TEXT INGESTION (manual) ────────────────────────

    class IngestTextRequest(BaseModel):
        texts: List[str]
        source_paths: List[str]

    @app.post("/internal/rag/ingest")
    async def ingest_text(req: IngestTextRequest):
        if len(req.texts) != len(req.source_paths):
            raise HTTPException(
                400, "texts and source_paths must be same length"
            )

        # Filter out empty/placeholder values
        valid_texts = []
        valid_paths = []
        for text, path in zip(req.texts, req.source_paths):
            if (
                text
                and text.strip()
                and text.strip() != "string"
            ):
                valid_texts.append(text)
                valid_paths.append(path)

        if not valid_texts:
            raise HTTPException(
                400,
                "No valid texts provided. "
                "Did you send Swagger placeholder values?",
            )

        vector_store.ingest(valid_texts, valid_paths)

        return {
            "status": "ingested",
            "count": len(valid_texts),
            "total": len(vector_store.documents),
        }

    # ─── SEARCH TEST (debug) ───────────────────────────

    class SearchRequest(BaseModel):
        query: str
        top_k: int = 5

    @app.post("/internal/rag/test-search")
    async def test_search(req: SearchRequest):
        """Test all 3 search strategies independently."""
        v = await vector_store.search(req.query, req.top_k)
        l = await local_search.search(req.query, req.top_k)
        s = await s3_search.search(req.query, req.top_k)

        return {
            "query": req.query,
            "vector": [
                {
                    "source": r.source_path,
                    "score": r.score,
                    "preview": r.content[:200],
                }
                for r in v
            ],
            "local": [
                {
                    "source": r.source_path,
                    "score": r.score,
                    "preview": r.content[:200],
                }
                for r in l
            ],
            "s3": [
                {
                    "source": r.source_path,
                    "score": r.score,
                    "preview": r.content[:200],
                }
                for r in s
            ],
        }

    # ─── LIST DOCUMENTS (debug) ────────────────────────

    @app.get("/internal/rag/documents")
    async def list_documents(
        limit: int = 20, offset: int = 0
    ):
        docs = vector_store.documents
        subset = docs[offset : offset + limit]

        return {
            "total": len(docs),
            "showing": f"{offset+1}-{offset+len(subset)}",
            "documents": [
                {
                    "index": offset + i,
                    "source": doc["source_path"],
                    "preview": doc["content"][:300],
                }
                for i, doc in enumerate(subset)
            ],
        }

    # ─── CLEAR VECTOR STORE ────────────────────────────

    @app.delete("/internal/rag/clear")
    async def clear_store():
        """Delete all documents from vector store."""
        count = len(vector_store.documents)
        vector_store.clear()
        return {
            "status": "cleared",
            "documents_deleted": count,
        }

    return app