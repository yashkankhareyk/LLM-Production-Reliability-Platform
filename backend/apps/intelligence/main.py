# Entrypoint for intelligence API
import uvicorn
from apps.intelligence.api.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "apps.intelligence.main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
    )