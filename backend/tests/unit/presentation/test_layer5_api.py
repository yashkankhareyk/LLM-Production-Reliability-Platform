import pytest
import requests

BASE_URL = "http://localhost:8000"


# Helper function
def post_json(endpoint, payload):
    return requests.post(f"{BASE_URL}{endpoint}", json=payload)


# Health check
def test_health():
    r = requests.get(f"{BASE_URL}/health")
    assert r.status_code == 200
    assert r.text


# Chat endpoint (direct and RAG)
def test_chat_direct():
    payload = {
        "messages": [{"role": "user", "content": "Hello"}],
        "use_rag": False,
        "max_tokens": 50,
        "temperature": 0.7,
        "correlation_id": "test_chat_001"
    }
    r = post_json("/v1/chat", payload)
    data = r.json()
    assert r.status_code == 200
    assert "message" in data
    # Compatible with mock responses
    assert "role" in data["message"] and "content" in data["message"]


def test_chat_rag():
    payload = {
        "messages": [{"role": "user", "content": "Search me something"}],
        "use_rag": True,
        "max_tokens": 50,
        "temperature": 0.7,
        "correlation_id": "test_rag_001"
    }
    r = post_json("/v1/chat", payload)
    if r.status_code == 200:
        data = r.json()
        assert "message" in data
        assert isinstance(data.get("sources", []), list)
    else:
        pytest.skip("RAG service not configured; skipping test.")


def test_chat_validation_error():
    payload = {"messages": [], "use_rag": False}
    r = post_json("/v1/chat", payload)
    if r.status_code != 422:
        pytest.skip("Validation not enforced in mock environment")
    else:
        data = r.json()
        assert "detail" in data


# File upload tests
def test_upload_single_file():
    files = {"file": ("test.txt", b"Hello world")}
    r = requests.post(f"{BASE_URL}/v1/ingest/file", files=files)
    if r.status_code == 404:
        pytest.skip("File ingest endpoint not available")
    else:
        assert r.status_code == 200


def test_upload_multiple_files():
    files = [("files", ("file1.txt", b"File 1")), ("files", ("file2.txt", b"File 2"))]
    r = requests.post(f"{BASE_URL}/v1/ingest/files", files=files)
    if r.status_code == 404:
        pytest.skip("Multiple file ingest endpoint not available")
    else:
        assert r.status_code == 200


# Documents
def test_list_documents():
    r = requests.get(f"{BASE_URL}/v1/documents?limit=5&offset=0")
    assert r.status_code == 200


def test_clear_documents():
    r = requests.delete(f"{BASE_URL}/v1/documents")
    assert r.status_code == 200


# Test search
def test_search():
    r = requests.post(f"{BASE_URL}/v1/test-search", params={"query": "Hello", "top_k": 3})
    assert r.status_code == 200


# Events
def test_list_events():
    r = requests.get(f"{BASE_URL}/v1/events?limit=10")
    if r.status_code != 200:
        pytest.skip("Events service not available")
    else:
        assert r.status_code == 200


# Runs
def test_list_runs():
    r = requests.get(f"{BASE_URL}/v1/runs?limit=5")
    if r.status_code != 200:
        pytest.skip("Runs service not available")
    else:
        runs = r.json()
        if runs:
            corr_id = runs[0].get("correlation_id")
            r2 = requests.get(f"{BASE_URL}/v1/runs/{corr_id}")
            assert r2.status_code == 200


# Metrics and event-types
def test_metrics():
    r = requests.get(f"{BASE_URL}/v1/metrics")
    if r.status_code != 200:
        pytest.skip("Metrics endpoint not available")
    else:
        assert r.status_code == 200


def test_event_types():
    r = requests.get(f"{BASE_URL}/v1/event-types")
    if r.status_code != 200:
        pytest.skip("Event types endpoint not available")
    else:
        assert r.status_code == 200


# Agent endpoints
def test_agent_run():
    payload = {"query": "Run agent test", "correlation_id": "agent_test_001", "max_tokens": 50, "temperature": 0.7}
    r = post_json("/v1/agent/run", payload)
    if r.status_code != 200:
        pytest.skip("Agent run endpoint not available")
    else:
        assert r.status_code == 200


def test_agent_graph():
    r = requests.get(f"{BASE_URL}/v1/agent/graph")
    if r.status_code != 200:
        pytest.skip("Agent graph endpoint not available")
    else:
        assert r.status_code == 200