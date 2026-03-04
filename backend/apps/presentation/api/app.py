import os
import httpx
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from dotenv import load_dotenv
from shared.schemas.chat import ChatRequest, ChatResponse

load_dotenv()

FOUNDATION_URL = os.getenv(
    "FOUNDATION_URL", "http://localhost:8001"
)
INTELLIGENCE_URL = os.getenv(
    "INTELLIGENCE_URL", "http://localhost:8002"
)


def create_app() -> FastAPI:
    app = FastAPI(title="Layer 5: API Gateway", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok", "layer": "presentation"}

    # ─── CHAT ───────────────────────────────────────────

    @app.post("/v1/chat", response_model=ChatResponse)
    async def public_chat(request: ChatRequest):
        try:
            if request.use_rag:
                url = f"{INTELLIGENCE_URL}/internal/rag/answer"
            else:
                url = f"{FOUNDATION_URL}/internal/llm/chat"

            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    url, json=request.model_dump()
                )
                resp.raise_for_status()
                return ChatResponse(**resp.json())

        except httpx.HTTPError as e:
            raise HTTPException(502, f"Service error: {e}")

    # ─── FILE UPLOAD ────────────────────────────────────

    @app.post("/v1/ingest/file")
    async def upload_file(file: UploadFile = File(...)):
        """Upload a single file (CSV, PDF, TXT)."""
        content = await file.read()

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{INTELLIGENCE_URL}/internal/rag/ingest/file",
                files={
                    "file": (file.filename, content, file.content_type)
                },
            )

            if resp.status_code != 200:
                raise HTTPException(
                    resp.status_code, resp.json()
                )

            return resp.json()

    # ─── MULTIPLE FILES UPLOAD ──────────────────────────

    @app.post("/v1/ingest/files")
    async def upload_files(
        files: List[UploadFile] = File(...),
    ):
        """Upload multiple files at once."""
        file_tuples = []
        for f in files:
            content = await f.read()
            file_tuples.append(
                ("files", (f.filename, content, f.content_type))
            )

        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{INTELLIGENCE_URL}/internal/rag/ingest/files",
                files=file_tuples,
            )

            if resp.status_code != 200:
                raise HTTPException(
                    resp.status_code, resp.json()
                )

            return resp.json()

    # ─── DOCUMENTS LIST ─────────────────────────────────

    @app.get("/v1/documents")
    async def list_documents(limit: int = 20, offset: int = 0):
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{INTELLIGENCE_URL}/internal/rag/documents",
                params={"limit": limit, "offset": offset},
            )
            return resp.json()

    # ─── CLEAR STORE ────────────────────────────────────

    @app.delete("/v1/documents")
    async def clear_documents():
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.delete(
                f"{INTELLIGENCE_URL}/internal/rag/clear"
            )
            return resp.json()

    # ─── SEARCH TEST ────────────────────────────────────

    @app.post("/v1/test-search")
    async def test_search(query: str, top_k: int = 5):
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{INTELLIGENCE_URL}/internal/rag/test-search",
                json={"query": query, "top_k": top_k},
            )
            return resp.json()

    return app