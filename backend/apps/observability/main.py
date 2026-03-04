# Entrypoint for observability query API
import uvicorn
from apps.observability.api.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "apps.observability.main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
    )