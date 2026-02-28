# FastAPI app factory (middleware, routers)
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Layer 1: Foundation", version="0.1.0")

    @app.get("/health")
    async def health():
        return {"status": "ok", "layer": "foundation", "version": "0.1.0"}

    return app