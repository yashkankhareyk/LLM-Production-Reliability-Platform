import os
import httpx
import logging
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Query,
)
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv

from shared.schemas.chat import ChatRequest, ChatResponse
from shared.utils.file_parser import parse_file
from apps.intelligence.core.rag_service import RAGService
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
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            f"{FOUNDATION_URL}/internal/llm/chat",
            json=request.model_dump(),
        )
        resp.raise_for_status()
        return ChatResponse(**resp.json())


def create_app() -> FastAPI:
    app = FastAPI(
        title="Layer 3: Intelligence",
        version="0.2.0",
        description="RAG service — upload files and ask questions",
    )

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

    rag_service = RAGService(
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
            "layer": "intelligence",
            "vector_docs": len(vector_store.documents),
        }

    # ─── RAG ANSWER ─────────────────────────────────

    @app.post(
        "/internal/rag/answer",
        response_model=ChatResponse,
    )
    async def rag_answer(request: ChatRequest):
        return await rag_service.answer(request)

    # ─── UPLOAD SINGLE FILE ─────────────────────────
    #     Swagger UI shows "Choose File" button

    @app.post(
        "/internal/rag/ingest/file",
        summary="Upload a file to ingest",
        description=(
            "Choose a CSV, PDF, or TXT file from your computer. "
            "It will be parsed, chunked, and stored in the vector store."
        ),
    )
    async def ingest_file(
        file: UploadFile = File(
            ...,
            description="Select a CSV, PDF, or TXT file",
        ),
    ):
        # Validate file type
        if not file.filename:
            raise HTTPException(400, "No filename provided")

        ext = file.filename.rsplit(".", 1)[-1].lower()
        allowed = ["csv", "pdf", "txt", "md"]

        if ext not in allowed:
            raise HTTPException(
                400,
                f"File type '.{ext}' not supported. "
                f"Allowed: {allowed}",
            )

        # Read file content
        content = await file.read()

        if len(content) == 0:
            raise HTTPException(400, "File is empty")

        logger.info(
            f"Uploading: {file.filename} "
            f"({len(content)} bytes, type: .{ext})"
        )

        # Parse file into text chunks
        texts, source_paths = parse_file(
            file.filename, content
        )

        if not texts:
            raise HTTPException(
                400,
                "Could not extract text from this file. "
                "Make sure it has content.",
            )

        # Store in vector store
        vector_store.ingest(texts, source_paths)

        return {
            "status": "success",
            "filename": file.filename,
            "file_size_bytes": len(content),
            "chunks_created": len(texts),
            "total_docs_in_store": len(
                vector_store.documents
            ),
            "sample_chunks": [
                {
                    "source": source_paths[i],
                    "preview": texts[i][:300],
                }
                for i in range(min(3, len(texts)))
            ],
        }

    # ─── UPLOAD MULTIPLE FILES ──────────────────────
    #     Swagger UI shows multiple "Choose File" buttons

    @app.post(
        "/internal/rag/ingest/files",
        summary="Upload multiple files at once",
    )
    async def ingest_files(
        files: List[UploadFile] = File(
            ...,
            description="Select one or more files (CSV, PDF, TXT)",
        ),
    ):
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
            "total_docs_in_store": len(
                vector_store.documents
            ),
        }

    # ─── TEXT INGESTION (manual) ────────────────────

    class IngestTextRequest(BaseModel):
        texts: List[str]
        source_paths: List[str]

    @app.post(
        "/internal/rag/ingest/text",
        summary="Ingest raw text manually",
    )
    async def ingest_text(req: IngestTextRequest):
        if len(req.texts) != len(req.source_paths):
            raise HTTPException(
                400,
                "texts and source_paths must be same length",
            )

        valid = [
            (t, p)
            for t, p in zip(req.texts, req.source_paths)
            if t and t.strip() and t.strip() != "string"
        ]

        if not valid:
            raise HTTPException(
                400, "No valid texts provided"
            )

        texts = [v[0] for v in valid]
        paths = [v[1] for v in valid]

        vector_store.ingest(texts, paths)

        return {
            "status": "ingested",
            "count": len(texts),
            "total": len(vector_store.documents),
        }

    # ─── SEARCH TEST ───────────────────────────────

    class SearchRequest(BaseModel):
        query: str
        top_k: int = 5

    @app.post(
        "/internal/rag/test-search",
        summary="Test search across all 3 strategies",
    )
    async def test_search(req: SearchRequest):
        v = await vector_store.search(
            req.query, req.top_k
        )
        l = await local_search.search(
            req.query, req.top_k
        )
        s = await s3_search.search(req.query, req.top_k)

        return {
            "query": req.query,
            "vector": [
                {
                    "source": r.source_path,
                    "score": r.score,
                    "content": r.content[:300],
                }
                for r in v
            ],
            "local": [
                {
                    "source": r.source_path,
                    "score": r.score,
                    "content": r.content[:300],
                }
                for r in l
            ],
            "s3": [
                {
                    "source": r.source_path,
                    "score": r.score,
                    "content": r.content[:300],
                }
                for r in s
            ],
        }

    # ─── LIST DOCUMENTS ────────────────────────────

    @app.get(
        "/internal/rag/documents",
        summary="See all stored documents",
    )
    async def list_documents(
        limit: int = Query(20, description="Max results"),
        offset: int = Query(0, description="Skip N results"),
    ):
        docs = vector_store.documents
        subset = docs[offset : offset + limit]

        return {
            "total": len(docs),
            "showing": f"{offset+1} to {offset+len(subset)}",
            "documents": [
                {
                    "index": offset + i,
                    "source": doc["source_path"],
                    "preview": doc["content"][:300],
                }
                for i, doc in enumerate(subset)
            ],
        }

    # ─── CLEAR STORE ───────────────────────────────

    @app.delete(
        "/internal/rag/clear",
        summary="Delete all documents",
    )
    async def clear_store():
        count = len(vector_store.documents)
        vector_store.clear()
        return {
            "status": "cleared",
            "documents_deleted": count,
        }

    return app