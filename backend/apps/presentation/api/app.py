# import os
# import httpx
# from fastapi import FastAPI, HTTPException
# from fastapi.middleware.cors import CORSMiddleware
# from dotenv import load_dotenv
# from shared.schemas.chat import ChatRequest, ChatResponse

# load_dotenv()

# FOUNDATION_URL = os.getenv("FOUNDATION_URL", "http://localhost:8001")


# def create_app() -> FastAPI:
#     app = FastAPI(title="Layer 5: API Gateway", version="0.1.0")

#     app.add_middleware(
#         CORSMiddleware,
#         allow_origins=["http://localhost:5173"],
#         allow_credentials=True,
#         allow_methods=["*"],
#         allow_headers=["*"],
#     )

#     @app.get("/health")
#     async def health():
#         return {"status": "ok", "layer": "presentation"}

#     @app.post("/v1/chat", response_model=ChatResponse)
#     async def public_chat(request: ChatRequest):
#         """
#         Public endpoint → calls Layer 1 internally.
#         Later: will also call Layer 3 (RAG) if use_rag=True.
#         """
#         try:
#             async with httpx.AsyncClient(timeout=60.0) as client:
#                 resp = await client.post(
#                     f"{FOUNDATION_URL}/internal/llm/chat",
#                     json=request.model_dump(),
#                 )
#                 resp.raise_for_status()
#                 return ChatResponse(**resp.json())
#         except httpx.HTTPError as e:
#             raise HTTPException(
#                 status_code=502,
#                 detail=f"Foundation service error: {str(e)}",
#             )

#     return app
import os

from fastapi import Query
from pypika import Query as PypikaQuery
from pydantic import BaseModel
import httpx
from typing import List
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from shared.schemas.chat import ChatRequest, ChatResponse

load_dotenv()

FOUNDATION_URL = os.getenv("FOUNDATION_URL", "http://localhost:8001")
INTELLIGENCE_URL = os.getenv("INTELLIGENCE_URL", "http://localhost:8002")
OBSERVABILITY_URL = os.getenv(
    "OBSERVABILITY_URL", "http://localhost:8003"
)

def create_app() -> FastAPI:
    app = FastAPI(title="Layer 5: API Gateway", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok", "layer": "presentation"}

     # ─── CHAT ───────────────────────────────────────

    @app.post(
        "/v1/chat",
        response_model=ChatResponse,
        summary="Chat — with or without RAG",
        description=(
            "Set use_rag=true to search uploaded documents. "
            "Set use_rag=false for direct LLM chat."
        ),
    )
    async def chat(request: ChatRequest):
        try:
            if request.use_rag:
                url = (
                    f"{INTELLIGENCE_URL}/internal/rag/answer"
                )
            else:
                url = (
                    f"{FOUNDATION_URL}/internal/llm/chat"
                )

            async with httpx.AsyncClient(
                timeout=60.0
            ) as client:
                resp = await client.post(
                    url, json=request.model_dump()
                )
                resp.raise_for_status()
                return ChatResponse(**resp.json())

        except httpx.HTTPError as e:
            raise HTTPException(
                502, f"Service error: {e}"
            )

    # ─── UPLOAD SINGLE FILE ─────────────────────────

    @app.post(
        "/v1/ingest/file",
        summary="Upload a file to ingest",
        description=(
            "Choose a CSV, PDF, or TXT file. "
            "It will be parsed and stored for RAG search."
        ),
    )
    async def upload_file(
        file: UploadFile = File(
            ...,
            description="Choose CSV, PDF, or TXT file",
        ),
    ):
        content = await file.read()

        async with httpx.AsyncClient(
            timeout=120.0
        ) as client:
            resp = await client.post(
                f"{INTELLIGENCE_URL}/internal/rag/ingest/file",
                files={
                    "file": (
                        file.filename,
                        content,
                        file.content_type,
                    )
                },
            )

            if resp.status_code != 200:
                detail = resp.text
                try:
                    detail = resp.json()
                except Exception:
                    pass
                raise HTTPException(
                    resp.status_code, detail
                )

            return resp.json()

    # ─── UPLOAD MULTIPLE FILES ──────────────────────

    @app.post(
        "/v1/ingest/files",
        summary="Upload multiple files at once",
    )
    async def upload_files(
        files: List[UploadFile] = File(
            ...,
            description="Choose one or more files",
        ),
    ):
        file_tuples = []
        for f in files:
            content = await f.read()
            file_tuples.append(
                (
                    "files",
                    (f.filename, content, f.content_type),
                )
            )

        async with httpx.AsyncClient(
            timeout=120.0
        ) as client:
            resp = await client.post(
                f"{INTELLIGENCE_URL}/internal/rag/ingest/files",
                files=file_tuples,
            )

            if resp.status_code != 200:
                raise HTTPException(
                    resp.status_code, resp.text
                )

            return resp.json()

    # ─── LIST DOCUMENTS ────────────────────────────

    @app.get(
        "/v1/documents",
        summary="View all ingested documents",
    )
    async def list_documents(
        limit: int = Query(20),
        offset: int = Query(0),
    ):
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            resp = await client.get(
                f"{INTELLIGENCE_URL}/internal/rag/documents",
                params={
                    "limit": limit,
                    "offset": offset,
                },
            )
            return resp.json()

    # ─── SEARCH TEST ───────────────────────────────

    class SearchTestRequest(BaseModel):
        query: str
        top_k: int = 5

    @app.post(
        "/v1/test-search",
        summary="Test search without calling LLM",
        description=(
            "See what the vector, local, and S3 search "
            "find for a query — useful for debugging."
        ),
    )
    async def test_search(req: SearchTestRequest):
        async with httpx.AsyncClient(
            timeout=30.0
        ) as client:
            resp = await client.post(
                f"{INTELLIGENCE_URL}/internal/rag/test-search",
                json=req.model_dump(),
            )
            return resp.json()

    # ─── CLEAR ALL DOCUMENTS ───────────────────────

    @app.delete(
        "/v1/documents",
        summary="Delete all ingested documents",
    )
    async def clear_documents():
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            resp = await client.delete(
                f"{INTELLIGENCE_URL}/internal/rag/clear"
            )
            return resp.json()
        
    # ─── OBSERVABILITY ENDPOINTS ────────────────────

    @app.get(
        "/v1/events",
        summary="View all events",
    )
    async def get_events(
        correlation_id: str = Query(None),
        event_type: str = Query(None),
        layer: str = Query(None),
        limit: int = Query(50),
    ):
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            resp = await client.get(
                f"{OBSERVABILITY_URL}/internal/obs/events",
                params={
                    "correlation_id": correlation_id,
                    "event_type": event_type,
                    "layer": layer,
                    "limit": limit,
                },
            )
            return resp.json()

    @app.get(
        "/v1/runs",
        summary="View all runs (grouped events)",
    )
    async def get_runs(limit: int = Query(20)):
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            resp = await client.get(
                f"{OBSERVABILITY_URL}/internal/obs/runs",
                params={"limit": limit},
            )
            return resp.json()

    @app.get(
        "/v1/runs/{correlation_id}",
        summary="View single run timeline",
    )
    async def get_run(correlation_id: str):
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            resp = await client.get(
                f"{OBSERVABILITY_URL}/internal/obs/runs/{correlation_id}",
            )
            return resp.json()

    @app.get(
        "/v1/metrics",
        summary="View platform metrics",
    )
    async def get_metrics():
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            resp = await client.get(
                f"{OBSERVABILITY_URL}/internal/obs/metrics",
            )
            return resp.json()

    @app.get(
        "/v1/event-types",
        summary="List all event types with counts",
    )
    async def get_event_types():
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            resp = await client.get(
                f"{OBSERVABILITY_URL}/internal/obs/event-types",
            )
            return resp.json()


    return app