"""Layer 5: Presentation — Public API Gateway + WebSocket."""
import os
import uuid
import httpx
import logging
from fastapi import (
    FastAPI,
    UploadFile,
    File,
    HTTPException,
    Query,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from shared.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    RetrievalSource,
)
from shared.events.event_bus import InMemoryEventBus
from apps.presentation.websocket.manager import ws_manager

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FOUNDATION_URL = os.getenv(
    "FOUNDATION_URL", "http://localhost:8001"
)
INTELLIGENCE_URL = os.getenv(
    "INTELLIGENCE_URL", "http://localhost:8002"
)
OBSERVABILITY_URL = os.getenv(
    "OBSERVABILITY_URL", "http://localhost:8003"
)
ORCHESTRATION_URL = os.getenv(
    "ORCHESTRATION_URL", "http://localhost:8004"
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="LLM Reliability Platform — API",
        version="0.5.0",
        description=(
            "Upload files, chat with RAG agent, "
            "view live events via WebSocket."
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Register WebSocket broadcaster with event bus ──
    bus = InMemoryEventBus()

    async def on_event(event):
        await ws_manager.broadcast_event(event)

    @app.on_event("startup")
    async def startup():
        await bus.subscribe(on_event)
        logger.info("📡 WebSocket broadcaster registered")

    # ═══════════════════════════════════════════════════
    #  HEALTH
    # ═══════════════════════════════════════════════════

    @app.get("/health")
    async def health():
        return {
            "status": "ok",
            "layer": "presentation",
            "version": "0.5.0",
            "websocket_connections": ws_manager.connection_count,
            "total_events": bus.total_events,
        }

    # ═══════════════════════════════════════════════════
    #  WEBSOCKET — Live Event Stream
    # ═══════════════════════════════════════════════════

    @app.websocket("/v1/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """
        Connect to receive live events in real-time.

        Commands you can send:
          "history"  → get last 50 events
          "metrics"  → get live metrics summary
          "ping"     → get pong response
          "status"   → get connection status
        """
        await ws_manager.connect(websocket)

        try:
            while True:
                data = await websocket.receive_text()

                if data == "history":
                    events = bus.get_events(limit=50)
                    await websocket.send_json(
                        {
                            "type": "history",
                            "count": len(events),
                            "events": [
                                {
                                    "event_id": e.event_id,
                                    "correlation_id": e.correlation_id,
                                    "event_type": e.event_type,
                                    "timestamp": e.timestamp.isoformat(),
                                    "layer": e.layer,
                                    "payload": e.payload,
                                }
                                for e in events
                            ],
                        }
                    )

                elif data == "metrics":
                    all_events = bus.get_events(limit=10000)

                    total_req = len(
                        [
                            e for e in all_events
                            if e.event_type == "llm.request.started"
                        ]
                    )
                    total_completed = len(
                        [
                            e for e in all_events
                            if e.event_type == "llm.request.completed"
                        ]
                    )
                    total_failed = len(
                        [
                            e for e in all_events
                            if "failed" in e.event_type
                        ]
                    )
                    total_agent = len(
                        [
                            e for e in all_events
                            if e.event_type == "agent.workflow.started"
                        ]
                    )

                    await websocket.send_json(
                        {
                            "type": "metrics",
                            "total_events": len(all_events),
                            "llm_requests": total_req,
                            "llm_completed": total_completed,
                            "llm_failures": total_failed,
                            "agent_runs": total_agent,
                            "ws_connections": ws_manager.connection_count,
                        }
                    )

                elif data == "ping":
                    await websocket.send_json(
                        {"type": "pong"}
                    )

                elif data == "status":
                    await websocket.send_json(
                        {
                            "type": "status",
                            "active_connections": ws_manager.connection_count,
                            "total_events": bus.total_events,
                        }
                    )

                else:
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": (
                                f"Unknown command: '{data}'. "
                                "Use: history, metrics, ping, status"
                            ),
                        }
                    )

        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)

    # ═══════════════════════════════════════════════════
    #  CHAT
    # ═══════════════════════════════════════════════════

    @app.post(
        "/v1/chat",
        response_model=ChatResponse,
        summary="Chat — direct LLM or RAG agent",
    )
    async def chat(request: ChatRequest):
        try:
            if request.use_rag:
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
                async with httpx.AsyncClient(
                    timeout=60.0
                ) as client:
                    resp = await client.post(
                        f"{FOUNDATION_URL}/internal/llm/chat",
                        json=request.model_dump(),
                    )
                    resp.raise_for_status()
                    return ChatResponse(**resp.json())

        except httpx.HTTPError as e:
            raise HTTPException(502, f"Service error: {e}")

    # ═══════════════════════════════════════════════════
    #  AGENT (full details)
    # ═══════════════════════════════════════════════════

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
    )
    async def run_agent(req: AgentRequest):
        async with httpx.AsyncClient(
            timeout=120.0
        ) as client:
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
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            resp = await client.get(
                f"{ORCHESTRATION_URL}/internal/agent/graph",
            )
            return resp.json()

    # ═══════════════════════════════════════════════════
    #  FILE UPLOAD
    # ═══════════════════════════════════════════════════

    @app.post(
        "/v1/ingest/file",
        summary="Upload a file (CSV, PDF, TXT)",
    )
    async def upload_file(
        file: UploadFile = File(
            ..., description="Choose a file to ingest"
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
                raise HTTPException(
                    resp.status_code, resp.text
                )
            return resp.json()

    @app.post(
        "/v1/ingest/files",
        summary="Upload multiple files",
    )
    async def upload_files(
        files: List[UploadFile] = File(...),
    ):
        file_tuples = []
        for f in files:
            content = await f.read()
            file_tuples.append(
                ("files", (f.filename, content, f.content_type))
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

    # ═══════════════════════════════════════════════════
    #  DOCUMENTS
    # ═══════════════════════════════════════════════════

    @app.get(
        "/v1/documents",
        summary="View ingested documents",
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
                params={"limit": limit, "offset": offset},
            )
            return resp.json()

    @app.delete(
        "/v1/documents",
        summary="Delete all documents",
    )
    async def clear_documents():
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            resp = await client.delete(
                f"{INTELLIGENCE_URL}/internal/rag/clear"
            )
            return resp.json()

    # ═══════════════════════════════════════════════════
    #  SEARCH TEST
    # ═══════════════════════════════════════════════════

    class SearchTestRequest(BaseModel):
        query: str
        top_k: int = 5

    @app.post(
        "/v1/test-search",
        summary="Test search without calling LLM",
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

    # ═══════════════════════════════════════════════════
    #  OBSERVABILITY
    # ═══════════════════════════════════════════════════

    @app.get("/v1/events", summary="View all events")
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

    @app.get("/v1/runs", summary="View all runs")
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

    @app.get("/v1/metrics", summary="Platform metrics")
    async def get_metrics():
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            resp = await client.get(
                f"{OBSERVABILITY_URL}/internal/obs/metrics",
            )
            return resp.json()

    @app.get("/v1/event-types", summary="Event type counts")
    async def get_event_types():
        async with httpx.AsyncClient(
            timeout=10.0
        ) as client:
            resp = await client.get(
                f"{OBSERVABILITY_URL}/internal/obs/event-types",
            )
            return resp.json()

    return app