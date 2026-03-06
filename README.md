# Updated README.md

```markdown
# LLM Production Reliability Platform

A modular platform for running LLM applications in production with **reliability**, **observability**, and **graceful degradation** by design.

This repo is organized into **5 decoupled layers** that communicate only via **contracts** (`shared/interfaces`, `shared/schemas`) and external interfaces (REST, WebSockets).

---

## What This Platform Does
```

User uploads files (CSV, PDF, TXT)
↓
Files are parsed, chunked, and stored as vectors (FAISS)
↓
User asks a question
↓
LangGraph agent searches: Vector → Local Files → S3
↓
Found context is injected into LLM prompt
↓
LLM generates answer (Grok → OpenRouter → Mock fallback)
↓
Every step emits events (visible in real-time via WebSocket)

```

---

## Why This Exists

LLM systems fail in predictable ways (provider outages, latency spikes, hallucinations, tool failures, runaway costs). This platform gives you:

- **Model/provider routing + automatic fallbacks** (Grok → OpenRouter → Mock)
- **RAG with 3-tier fallback** (Vector → Local files → S3 storage)
- **LangGraph agent orchestration** (stateful workflow with conditional branching)
- **Event-driven observability** (every action emits an event)
- **Real-time monitoring** (WebSocket live event stream)
- **File ingestion** (CSV, PDF, TXT parsing and vector embedding)
- **Layered architecture** so components can be replaced without rewrites

---

## Architecture (5 Layers)

```

┌─────────────────────────────────────────────────────────────────┐
│ LAYER 5: PRESENTATION │ API Gateway + WebSocket + Dashboard │
│ :8000 │ Single entry point for all clients │
└──────────────────────────┬──────────────────────────────────────┘
│
┌──────────────────────────▼──────────────────────────────────────┐
│ LAYER 4: OBSERVABILITY │ Events + Runs + Metrics + Tracking │
│ :8003 │ Collects and queries all system events│
└──────────────────────────┬──────────────────────────────────────┘
│
┌──────────────────────────▼──────────────────────────────────────┐
│ LAYER 3: INTELLIGENCE │ File Ingestion + Vector Store + RAG │
│ :8002 │ Handles document storage and search │
└──────────────────────────┬──────────────────────────────────────┘
│
┌──────────────────────────▼──────────────────────────────────────┐
│ LAYER 2: ORCHESTRATION │ LangGraph Agent + Stateful Workflows │
│ :8004 │ Orchestrates RAG fallback chain │
└──────────────────────────┬──────────────────────────────────────┘
│
┌──────────────────────────▼──────────────────────────────────────┐
│ LAYER 1: FOUNDATION │ LLM Gateway + Router + Fallbacks │
│ :8001 │ Talks to Grok, OpenRouter, Mock │
└─────────────────────────────────────────────────────────────────┘

```

### How Layers Communicate

```

Frontend ──HTTP/WS──→ Layer 5 (:8000)

Layer 5 ──HTTP──→ Layer 1 (:8001) for direct chat
Layer 5 ──HTTP──→ Layer 2 (:8004) for RAG agent
Layer 5 ──HTTP──→ Layer 3 (:8002) for file ingestion
Layer 5 ──HTTP──→ Layer 4 (:8003) for events/metrics

Layer 2 ──HTTP──→ Layer 1 (:8001) for LLM calls
Layer 2 reads ──→ data/vector_store (FAISS index)
Layer 2 reads ──→ data/local_docs (local files)
Layer 2 reads ──→ data/s3_mock (S3 mock files)

Layer 3 writes ─→ data/vector_store (FAISS index)

All Layers ─emit─→ InMemoryEventBus ─→ Layer 4 (storage/query)
─→ Layer 5 (WebSocket broadcast)

RULE: No layer imports code from another layer.
Only shared/ schemas and HTTP calls.

```

---

## Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.11+** | Backend language |
| **FastAPI** | Async REST API + WebSocket + auto-docs (Swagger) |
| **LangGraph** | Stateful agent workflow (conditional branching) |
| **FAISS** | Local vector similarity search |
| **sentence-transformers** | Text → embedding vectors (all-MiniLM-L6-v2) |
| **Grok API** | Primary LLM provider |
| **OpenRouter API** | Fallback LLM provider |
| **Pydantic** | Schema validation for all contracts |
| **httpx** | Async HTTP client for inter-layer calls |
| **WebSocket** | Real-time event streaming |
| **React + Vite** | Frontend dashboard (separate development) |

---

## Repository Structure

```

llm-reliability-platform/
├── backend/
│ ├── pyproject.toml
│ ├── .env
│ ├── .env.example
│ │
│ ├── shared/ # Contracts between all layers
│ │ ├── schemas/
│ │ │ ├── chat.py # ChatRequest, ChatResponse, RetrievalSource
│ │ │ └── events.py # EventEnvelope
│ │ ├── interfaces/
│ │ │ ├── retrieval.py # RetrievalStrategy (abstract)
│ │ │ └── event_bus.py # EventPublisher, EventSubscriber (abstract)
│ │ ├── events/
│ │ │ ├── event_bus.py # InMemoryEventBus (singleton)
│ │ │ └── publisher.py # emit_event() helper
│ │ └── utils/
│ │ └── file_parser.py # CSV, PDF, TXT parsing + chunking
│ │
│ ├── apps/
│ │ ├── foundation/ # LAYER 1: LLM Gateway (:8001)
│ │ │ ├── main.py
│ │ │ ├── api/
│ │ │ │ └── app.py # POST /internal/llm/chat
│ │ │ ├── core/
│ │ │ │ └── llm_service.py # Routing + fallback logic
│ │ │ └── providers/
│ │ │ ├── base.py # LLMProvider interface
│ │ │ ├── grok_adapter.py # Grok API adapter
│ │ │ ├── openrouter_adapter.py # OpenRouter adapter
│ │ │ └── mock_adapter.py # Mock provider (testing)
│ │ │
│ │ ├── orchestration/ # LAYER 2: LangGraph Agent (:8004)
│ │ │ ├── main.py
│ │ │ ├── api/
│ │ │ │ └── app.py # POST /internal/agent/run
│ │ │ └── core/
│ │ │ ├── state.py # RAGState (TypedDict)
│ │ │ ├── nodes.py # Graph nodes (search, evaluate, generate)
│ │ │ └── graph.py # LangGraph builder + RAGAgent class
│ │ │
│ │ ├── intelligence/ # LAYER 3: File Ingestion + Search (:8002)
│ │ │ ├── main.py
│ │ │ ├── api/
│ │ │ │ └── app.py # POST /internal/rag/ingest/file
│ │ │ ├── core/
│ │ │ │ └── rag_service.py # RAG pipeline (search + augment + call LLM)
│ │ │ └── retrieval/
│ │ │ ├── vector_store.py # FAISS vector search
│ │ │ ├── local_search.py # Keyword search in local files
│ │ │ └── s3_search.py # Keyword search in S3 mock
│ │ │
│ │ ├── observability/ # LAYER 4: Events + Metrics (:8003)
│ │ │ ├── main.py
│ │ │ └── api/
│ │ │ └── app.py # GET /internal/obs/events, /runs, /metrics
│ │ │
│ │ └── presentation/ # LAYER 5: API Gateway + WebSocket (:8000)
│ │ ├── main.py
│ │ ├── api/
│ │ │ └── app.py # All /v1/\* public endpoints + WS /v1/ws
│ │ └── websocket/
│ │ └── manager.py # ConnectionManager for WebSocket broadcast
│ │
│ ├── data/
│ │ ├── vector_store/ # FAISS index + documents.json
│ │ ├── local_docs/ # .txt files for local keyword search
│ │ └── s3_mock/ # .txt files simulating S3 storage
│ │
│ ├── test_websocket.py # WebSocket test client
│ └── ingest_csv.py # CSV ingestion script
│
├── frontend/ # React dashboard (separate development)
│ ├── package.json
│ └── src/
│
├── infra/
│ └── docker-compose.yml
│
└── docs/
└── ARCHITECTURE.md

````

---

## Quick Start
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


# Service URLs
FOUNDATION_URL=http://localhost:8001
INTELLIGENCE_URL=http://localhost:8002
OBSERVABILITY_URL=http://localhost:8003
ORCHESTRATION_URL=http://localhost:8004

# Data paths
VECTOR_STORE_PATH=./data/vector_store
LOCAL_DOCS_PATH=./data/local_docs
S3_MOCK_PATH=./data/s3_mock
```

### 3) Create Data Directories

```bash
mkdir -p data/vector_store data/local_docs data/s3_mock
```

### 4) Start All 5 Services

```bash
# Terminal 1: Layer 1 — Foundation (LLM Gateway)
python -m apps.foundation.main                    # :8001

# Terminal 2: Layer 3 — Intelligence (File Ingestion + Search)
python -m apps.intelligence.main                   # :8002

# Terminal 3: Layer 4 — Observability (Events + Metrics)
python -m apps.observability.main                  # :8003

# Terminal 4: Layer 2 — Orchestration (LangGraph Agent)
python -m apps.orchestration.main                  # :8004

# Terminal 5: Layer 5 — Presentation (API Gateway + WebSocket)
python -m apps.presentation.main                   # :8000
```

### 5) Health Checks

```bash
curl http://localhost:8001/health   # Foundation
curl http://localhost:8002/health   # Intelligence
curl http://localhost:8003/health   # Observability
curl http://localhost:8004/health   # Orchestration
curl http://localhost:8000/health   # Presentation
```

### 6) Upload a File

```bash
# Via Swagger UI (recommended)
open http://localhost:8000/docs
# → POST /v1/ingest/file → Try it out → Choose File → Execute

# Or via curl
curl -X POST http://localhost:8000/v1/ingest/file \
  -F "file=@your_data.csv"
```

### 7) Ask a Question

```bash
# With RAG (searches uploaded documents)
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "your question here"}],
    "use_rag": true,
    "max_tokens": 512
  }'

# Direct LLM (no document search)
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "what is python?"}],
    "use_rag": false
  }'
```

### 8) Run Agent (Full Step Details)

```bash
curl -X POST http://localhost:8000/v1/agent/run \
  -H "Content-Type: application/json" \
  -d '{
    "query": "your question here",
    "max_tokens": 512
  }'
```

Response includes `search_path`, `step_details`, and `sources`.

### 9) WebSocket (Live Events)

```bash
# Terminal 6: Start WebSocket test client
python test_websocket.py

# Then send a chat request in another terminal
# Watch events appear in real-time
```

Or connect from browser console:

```javascript
const ws = new WebSocket("ws://localhost:8000/v1/ws");
ws.onmessage = (e) => console.log(JSON.parse(e.data));
ws.onopen = () => ws.send("history"); // get past events
```

---

## API Reference

### Public Endpoints (Layer 5 — :8000)

| Method   | Endpoint           | Description                        |
| -------- | ------------------ | ---------------------------------- |
| `WS`     | `/v1/ws`           | WebSocket live event stream        |
| `POST`   | `/v1/chat`         | Chat with or without RAG           |
| `POST`   | `/v1/agent/run`    | Run LangGraph agent (full details) |
| `GET`    | `/v1/agent/graph`  | View agent workflow graph          |
| `POST`   | `/v1/ingest/file`  | Upload single file (CSV/PDF/TXT)   |
| `POST`   | `/v1/ingest/files` | Upload multiple files              |
| `GET`    | `/v1/documents`    | View ingested documents            |
| `DELETE` | `/v1/documents`    | Clear all documents                |
| `POST`   | `/v1/test-search`  | Test search without calling LLM    |
| `GET`    | `/v1/events`       | View all events (filterable)       |
| `GET`    | `/v1/runs`         | View all runs (grouped by request) |
| `GET`    | `/v1/runs/{id}`    | Single run timeline                |
| `GET`    | `/v1/metrics`      | Platform metrics                   |
| `GET`    | `/v1/event-types`  | Event type counts                  |

### Internal Endpoints

| Layer            | Port | Endpoint                         | Description            |
| ---------------- | ---- | -------------------------------- | ---------------------- |
| L1 Foundation    | 8001 | `POST /internal/llm/chat`        | Call LLM with fallback |
| L2 Orchestration | 8004 | `POST /internal/agent/run`       | Run LangGraph agent    |
| L2 Orchestration | 8004 | `GET /internal/agent/graph`      | Agent graph structure  |
| L3 Intelligence  | 8002 | `POST /internal/rag/ingest/file` | Upload and parse file  |
| L3 Intelligence  | 8002 | `POST /internal/rag/answer`      | RAG pipeline           |
| L3 Intelligence  | 8002 | `POST /internal/rag/test-search` | Test search strategies |
| L3 Intelligence  | 8002 | `GET /internal/rag/documents`    | List stored documents  |
| L3 Intelligence  | 8002 | `DELETE /internal/rag/clear`     | Clear vector store     |
| L4 Observability | 8003 | `GET /internal/obs/events`       | Query events           |
| L4 Observability | 8003 | `GET /internal/obs/runs`         | Query runs             |
| L4 Observability | 8003 | `GET /internal/obs/runs/{id}`    | Single run detail      |
| L4 Observability | 8003 | `GET /internal/obs/metrics`      | Aggregated metrics     |

### Swagger UI (Interactive Docs)

```
http://localhost:8000/docs   ← All public endpoints
http://localhost:8001/docs   ← Foundation
http://localhost:8002/docs   ← Intelligence
http://localhost:8003/docs   ← Observability
http://localhost:8004/docs   ← Orchestration
```

---

## LangGraph Agent Workflow

```
START
  │
  ▼
┌──────────────┐
│vector_search │ Search FAISS index (semantic similarity)
└──────┬───────┘
       ▼
┌──────────────────┐
│evaluate_vector   │ Score >= 0.45?
└──┬──────────┬────┘
   │          │
  YES         NO
   │          ▼
   │   ┌──────────────┐
   │   │local_search  │ Keyword search in data/local_docs/
   │   └──────┬───────┘
   │          ▼
   │   ┌──────────────────┐
   │   │evaluate_local   │ Found results?
   │   └──┬──────────┬───┘
   │      │          │
   │    YES          NO
   │      │          ▼
   │      │   ┌──────────────┐
   │      │   │s3_search     │ Keyword search in data/s3_mock/
   │      │   └──────┬───────┘
   │      │          │
   ▼      ▼          ▼
┌──────────────────────┐
│select_sources       │ Pick best results from all searches
└──────────┬──────────┘
           ▼
┌──────────────────────┐
│generate              │ Call LLM (Layer 1) with context
└──────────┬──────────┘
           ▼
         END
```

---

## Event System

### Event Types

```
Layer 1 (Foundation):
  llm.request.started        → LLM request received
  llm.provider.trying        → Attempting provider X
  llm.provider.success       → Provider X responded
  llm.provider.failed        → Provider X error
  llm.request.completed      → Final response ready
  llm.request.all_failed     → Every provider failed

Layer 2 (Orchestration):
  agent.workflow.started     → Agent began processing
  agent.node.started         → Entering graph node
  agent.node.completed       → Node finished
  agent.node.decision        → Branch point reached
  agent.workflow.completed   → Agent finished
  agent.workflow.failed      → Agent error

Layer 3 (Intelligence):
  rag.request.started        → RAG pipeline started
  rag.search.started         → Search initiated
  rag.search.*.completed     → Search results ready
  rag.request.completed      → RAG response ready
```

### Correlation ID

Every request gets a `correlation_id`. All events across all layers share this ID, enabling full request tracing:

```bash
# View complete timeline for one request
curl http://localhost:8000/v1/runs/YOUR_CORRELATION_ID
```

### WebSocket Commands

```
Connect: ws://localhost:8000/v1/ws

Send:
  "history"   → get last 50 events
  "metrics"   → get live metrics summary
  "ping"      → health check (returns pong)
  "status"    → connection count + event count

Receive:
  { "type": "event", "event_type": "...", "layer": "...", "payload": {...} }
```

---

## Request Flows

### Direct Chat (No RAG)

```
Frontend → Layer 5 → Layer 1 → Grok/OpenRouter/Mock → Response
                                    (auto-fallback)
```

### RAG Chat (With Agent)

```
Frontend → Layer 5 → Layer 2 (LangGraph Agent)
                         │
                         ├→ Vector Search (FAISS)
                         ├→ Local Search (keyword)    ← only if vector misses
                         ├→ S3 Search (keyword)       ← only if local misses
                         │
                         ├→ Select Best Sources
                         │
                         └→ Layer 1 (LLM with context) → Response
```

### File Ingestion

```
Frontend → Layer 5 → Layer 3 → Parse (CSV/PDF/TXT)
                                  → Chunk (500 chars, 50 overlap)
                                  → Embed (sentence-transformers)
                                  → Store (FAISS index on disk)
```

---

## Key Principles

- **Single responsibility per module** (no giant files)
- **No cross-layer imports** (only `shared/*` is shared)
- **Event-driven observability** (every action emits an event)
- **Graceful degradation** (Grok → OpenRouter → Mock; Vector → Local → S3)
- **Configuration over code** (API keys, URLs via `.env`)
- **Working code at every milestone** (incremental development)

---

## Development Milestones

| Tag      | Milestone       | What's Working                                |
| -------- | --------------- | --------------------------------------------- |
| `v0.0.1` | Skeleton        | All services start, health checks pass        |
| `v0.1.0` | Direct Chat     | Chat with Grok/OpenRouter, auto-fallback      |
| `v0.2.0` | RAG + Ingestion | Upload files, vector/local/S3 search          |
| `v0.3.0` | Events          | Every action emits events, queryable API      |
| `v0.4.0` | LangGraph       | Agent orchestrates retrieval with state graph |
| `v0.5.0` | WebSocket       | Live event stream to connected clients        |

---

## Team Workflow

### Branch Strategy

```
main (protected) ← always stable/runnable
feat/<name>      ← one task per branch, short-lived
```

### Work Allocation (4-person team)

```
Person A: Layer 1 (Foundation) + Layer 2 (Orchestration)
Person B: Layer 3 (Intelligence) + Layer 4 (Observability)
Person C: Layer 5 (Presentation)
Person D: Frontend (React dashboard)
```

### Contribution Rules

- No cross-layer imports. Only import from `shared/`.
- Keep files small and single-responsibility.
- Emit events for significant actions.
- Update `shared/schemas` first when changing API shapes.

---

## Future Enhancements

```
Layer 1: Redis cache, token budgets, new providers (Anthropic, Gemini)
Layer 2: Query rewriter node, reranker node, hallucination checker
Layer 3: DOCX/HTML support, replace FAISS with Pinecone/Weaviate, real S3
Layer 4: PostgreSQL storage, Grafana dashboards, Slack alerting
Layer 5: JWT auth, API key management, rate limiting, nginx deployment
```

---

## Testing

```bash
# Run all tests
cd backend
pytest -q

# Test specific layer
pytest tests/unit/test_router.py
pytest tests/contract/test_schemas_chat.py
pytest tests/integration/test_e2e_mvp.py
```

---

## License

TBD

```

```
````
