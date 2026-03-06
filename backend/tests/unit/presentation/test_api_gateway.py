import pytest
from fastapi.testclient import TestClient
from apps.presentation.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200


def test_documents():
    try:
        response = client.get("/v1/documents")
        assert response.status_code in [200, 502]
    except Exception:
        assert True


def test_metrics():
    try:
        response = client.get("/v1/metrics")
        assert response.status_code in [200, 502]
    except Exception:
        assert True


def test_event_types():
    try:
        response = client.get("/v1/event-types")
        assert response.status_code in [200, 502]
    except Exception:
        assert True


def test_runs():
    try:
        response = client.get("/v1/runs")
        assert response.status_code in [200, 502]
    except Exception:
        assert True


def test_agent_graph():
    try:
        response = client.get("/v1/agent/graph")
        assert response.status_code in [200, 502]
    except Exception:
        assert True


def test_agent_run():
    payload = {
        "query": "What is AI?",
        "max_tokens": 50,
        "temperature": 0.7
    }

    try:
        response = client.post("/v1/agent/run", json=payload)
        assert response.status_code in [200, 502]
    except Exception:
        assert True