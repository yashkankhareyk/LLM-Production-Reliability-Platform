# Entrypoint for orchestration API
import uvicorn
from apps.orchestration.api.app import create_app

app = create_app()

if __name__ == "__main__":
    uvicorn.run(
        "apps.orchestration.main:app",
        host="0.0.0.0",
        port=8004,
        reload=True,
    )