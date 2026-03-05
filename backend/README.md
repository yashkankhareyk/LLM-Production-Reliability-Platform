# LLM Production Reliability Platform – Backend

Backend service for monitoring, evaluating, and improving the reliability of LLM-powered systems. Built with FastAPI using a layered, modular architecture for production-ready deployments.

---

## 🚀 Tech Stack

- **FastAPI** – API framework
- **Uvicorn** – ASGI server
- **Pydantic v2** – Data validation
- **Redis** – Caching / state management
- **LangChain / LangGraph** – LLM orchestration
- **FAISS** – Vector search
- **Sentence Transformers** – Embeddings
- **Docker** – Infrastructure services

---

## 📂 Project Structure

```
backend/
│
├── apps/
│   ├── foundation/        # Core LLM logic (Layer 1)
│   └── presentation/      # API exposure layer (Layer 5)
│
├── shared/                # Shared utilities & domain logic
├── configs/               # Configuration management
│
├── pyproject.toml
└── README.md
```

---

## 🧠 Architecture Overview

This system follows a layered architecture:

- **Layer 1 – Foundation**
  - LLM orchestration
  - Provider selection
  - Fallback handling (Grok → OpenRouter)
  - Reliability evaluation

- **Layer 5 – Presentation**
  - REST API exposure
  - Health checks
  - Frontend integration

- **Infra Layer**
  - Redis
  - Vector services
  - Containerized dependencies

Separation ensures:

- Clean modularity
- Provider abstraction
- Scalable orchestration logic
- Clear reliability boundaries

⚙️ Setup
1️⃣ Create Virtual Environment
python -m venv venv
venv\Scripts\activate
2️⃣ Install Dependencies
pip install --upgrade pip
pip install -e ".[dev,llm,vector]"
🔐 Environment Variables

Create .env inside backend/:

OPENAI_API_KEY=
OPENROUTER_API_KEY=
GROK_API_KEY=
REDIS_URL=redis://localhost:6379
▶️ Running the System
🐳 Option A — With Docker (Recommended for Full Stack)

This runs infrastructure like Redis and vector services.

1️⃣ Start Infrastructure
cd infra
docker compose up -d
2️⃣ Start Backend Services

From backend/:

# Layer 1 – Foundation

python -m apps.foundation.main # http://localhost:8001

# Layer 3 – Intelligence

python -m apps.intelligence.main # http://localhost:8002

# Layer 5 – Presentation

python -m apps.presentation.main # http://localhost:8000

Health checks:

http://localhost:8000/health
http://localhost:8001/health
💻 Option B — Without Docker (Minimal Development Mode)

Use this if you don’t need Redis or external infra.

From backend/:

uvicorn apps.foundation.main:app --port 8001 --reload
uvicorn apps.intelligence.main:app --port 8002 --reload
uvicorn apps.presentation.main:app --port 8000 --reload

⚠️ Ensure:

Redis is disabled or mocked

Vector services are local (FAISS)

🧪 Run Tests
pytest

---

## 📦 Dependency Groups

### Core

Runtime server dependencies.

### dev

- pytest
- pytest-asyncio
- ruff

### llm

- openai
- langchain
- langchain-openai
- langgraph

### vector

- faiss-cpu
- sentence-transformers
- langchain-community

---

## 🛠 Future Improvements

- Dockerized backend container
- CI/CD pipelines
- Structured logging (JSON logs)
- Metrics + tracing (OpenTelemetry)
- Production environment profiles
- Centralized provider health monitoring

---

## 📌 Development Notes

- Python 3.11+
- Modern `pyproject.toml` packaging
- Editable install recommended
- Consider `src/` layout for larger scale
- Ensure `.env` loads via `python-dotenv`
