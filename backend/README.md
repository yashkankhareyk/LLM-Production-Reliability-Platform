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

---

## ⚙️ Setup Instructions

### 1️⃣ Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
```

### 2️⃣ Upgrade Packaging Tools

```bash
python -m pip install --upgrade pip setuptools wheel
```

### 3️⃣ Install Dependencies (Editable Mode)

```bash
pip install -e ".[dev]"
```

Optional dependency groups:

```bash
pip install -e ".[dev,llm,vector]"
```

---

## 🔐 Environment Variables

Create a `.env` file inside `backend/`:

```
OPENAI_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
GROK_API_KEY=your_key_here
REDIS_URL=redis://localhost:6379
```

⚠️ `.env` must exist in the `backend/` directory if running from there.

---

# ▶️ Running the Full System (Local Development)

## Option A – With Infrastructure (Recommended)

### Terminal 1 – Infrastructure

```bash
cd infra
docker compose up -d
```

### Terminal 2 – Layer 1 (Foundation)

```bash
cd backend
pip install -e ".[dev]"
pip install -e ".[dev,llm,vector]"
python -m apps.foundation.main
```

Health check:

```
http://localhost:8001/health
```

Expected:

```json
{ "status": "ok" }
```

# Terminal 2: Layer 3 (Intelligence)

python -m apps.intelligence.main # port 8002

### Terminal 3 – Layer 5 (Presentation)

```bash
python -m apps.presentation.main
```

Health check:

```
http://localhost:8000/health
```

---

### Terminal 4 – Frontend

```bash
cd frontend
npm install
npm run dev
```

Open:

```
http://localhost:5173
```

Expected:

- "Backend: ok"
- Type "Hello"
- Response from Grok
- If Grok fails → automatic fallback to OpenRouter

---

## Option B – Without Docker (Minimal Mode)

### Terminal 1 – Layer 1

```bash
cd backend
python -m apps.foundation.main
```

### Terminal 2 – Layer 5

```bash
python -m apps.presentation.main
```

### Terminal 3 – Frontend

```bash
cd frontend
npm run dev
```

---

## 🧪 Running Tests

```bash
pytest
```

---

## 🧹 Linting

```bash
ruff check .
```

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
