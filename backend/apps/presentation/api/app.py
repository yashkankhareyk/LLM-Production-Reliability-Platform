<<<<<<< Updated upstream
import os
=======

import os

from fastapi import Query
from pypika import Query as PypikaQuery
>>>>>>> Stashed changes
import httpx
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Query,
)
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from dotenv import load_dotenv
import uuid
from pydantic import BaseModel, Field
from shared.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    RetrievalSource,
)

load_dotenv()

FOUNDATION_URL = os.getenv(
    "FOUNDATION_URL", "http://localhost:8001"
)
INTELLIGENCE_URL = os.getenv(
    "INTELLIGENCE_URL", "http://localhost:8002"
)
OBSERVABILITY_URL = os.getenv(
    "OBSERVABILITY_URL", "http://localhost:8003"
)
<<<<<<< Updated upstream


=======
ORCHESTRATION_URL = os.getenv(
    "ORCHESTRATION_URL", "http://localhost:8004"
)
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
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
=======
    @app.post(
        "/v1/chat",
        response_model=ChatResponse,
        summary="Chat — direct LLM or RAG agent",
    )
    async def chat(request: ChatRequest):
        try:
            if request.use_rag:
                # ── Use LangGraph Agent (Layer 2) ──
                async with httpx.AsyncClient(
                    timeout=120.0
                ) as client:
                    resp = await client.post(
                        f"{ORCHESTRATION_URL}/internal/agent/run",
                        json={
                            "query": request.messages[-1].content,
                            "correlation_id": request.correlation_id,
                            "max_tokens": request.max_tokens,
                            "temperature": request.temperature,
                        },
                    )
                    resp.raise_for_status()
                    data = resp.json()

                    return ChatResponse(
                        message=ChatMessage(
                            role="assistant",
                            content=data["answer"],
                        ),
                        provider=data.get("provider", "unknown"),
                        model=data.get("model", "unknown"),
                        sources=[
                            RetrievalSource(**s)
                            for s in data.get("sources", [])
                        ],
                        tokens_used=data.get("tokens_used", 0),
                        latency_ms=data.get("total_latency_ms", 0),
                        correlation_id=data.get(
                            "correlation_id",
                            request.correlation_id,
                        ),
                    )
            else:
                # ── Direct LLM (Layer 1) ───────────
                async with httpx.AsyncClient(
                    timeout=60.0
                ) as client:
                    resp = await client.post(
                        f"{FOUNDATION_URL}/internal/llm/chat",
                        json=request.model_dump(),
                    )
                    resp.raise_for_status()
                    return ChatResponse(**resp.json())
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
=======

        # ─── AGENT (full step details) ──────────────────

    class AgentRequest(BaseModel):
        query: str
        correlation_id: str = Field(
            default_factory=lambda: str(uuid.uuid4())
        )
        max_tokens: int = 512
        temperature: float = 0.7

    @app.post(
        "/v1/agent/run",
        summary="Run agent — returns full step details",
        description=(
            "Same as /v1/chat with use_rag=true but returns "
            "search_path, step_details, and timing for each node."
        ),
    )
    async def run_agent(req: AgentRequest):
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{ORCHESTRATION_URL}/internal/agent/run",
                json=req.model_dump(),
            )
            resp.raise_for_status()
            return resp.json()

    @app.get(
        "/v1/agent/graph",
        summary="View agent workflow graph",
    )
    async def get_graph():
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{ORCHESTRATION_URL}/internal/agent/graph",
            )
            return resp.json()

>>>>>>> Stashed changes
    return app