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
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from shared.schemas.chat import ChatRequest, ChatResponse

load_dotenv()

FOUNDATION_URL = os.getenv("FOUNDATION_URL", "http://localhost:8001")
INTELLIGENCE_URL = os.getenv("INTELLIGENCE_URL", "http://localhost:8002")


def create_app() -> FastAPI:
    app = FastAPI(title="Layer 5: API Gateway", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "ok", "layer": "presentation"}

    @app.post("/v1/chat", response_model=ChatResponse)
    async def public_chat(request: ChatRequest):
        try:
            if request.use_rag:
                # Route to Layer 3 (Intelligence)
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        f"{INTELLIGENCE_URL}/internal/rag/answer",
                        json=request.model_dump(),
                    )
                    resp.raise_for_status()
                    return ChatResponse(**resp.json())
            else:
                # Route directly to Layer 1 (Foundation)
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
                detail=f"Service error: {str(e)}",
            )

    # Proxy ingestion to Layer 3
    from pydantic import BaseModel
    from typing import List

    class IngestRequest(BaseModel):
        texts: List[str]
        source_paths: List[str]

    @app.post("/v1/ingest")
    async def ingest(req: IngestRequest):
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{INTELLIGENCE_URL}/internal/rag/ingest",
                json=req.model_dump(),
            )
            resp.raise_for_status()
            return resp.json()

    return app