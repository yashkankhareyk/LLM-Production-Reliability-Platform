import os
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from shared.schemas.chat import ChatRequest, ChatResponse

load_dotenv()

FOUNDATION_URL = os.getenv("FOUNDATION_URL", "http://localhost:8001")


def create_app() -> FastAPI:
    app = FastAPI(title="Layer 5: API Gateway", version="0.1.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok", "layer": "presentation"}

    @app.post("/v1/chat", response_model=ChatResponse)
    async def public_chat(request: ChatRequest):
        """
        Public endpoint → calls Layer 1 internally.
        Later: will also call Layer 3 (RAG) if use_rag=True.
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.post(
                    f"{FOUNDATION_URL}/internal/llm/chat",
                    json=request.model_dump(),
                )
                resp.raise_for_status()
                return ChatResponse(**resp.json())
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Foundation service error: {str(e)}",
            )

    return app