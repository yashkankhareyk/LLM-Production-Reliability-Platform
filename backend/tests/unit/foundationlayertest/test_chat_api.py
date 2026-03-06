import pytest
from fastapi.testclient import TestClient
from apps.foundation.api.app import create_app

app = create_app()
client = TestClient(app)


# ==============================
# Test Chat API Success
# ==============================
def test_chat_api_success():

    response = client.post(
        "/internal/llm/chat",
        json={
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "message" in data
    assert "provider" in data
    assert "model" in data
    assert "tokens_used" in data
    assert "latency_ms" in data


# ==============================
# Test Missing Messages
# ==============================
def test_chat_api_missing_messages():

    response = client.post(
        "/internal/llm/chat",
        json={}
    )

    assert response.status_code == 422


# ==============================
# Test Empty Messages
# ==============================
def test_chat_api_empty_messages():

    response = client.post(
        "/internal/llm/chat",
        json={
            "messages": []
        }
    )

    assert response.status_code in [200, 422]


# ==============================
# Test Invalid Message Structure
# ==============================
def test_chat_api_invalid_message():

    response = client.post(
        "/internal/llm/chat",
        json={
            "messages": [
                {"role": "user"}
            ]
        }
    )

    assert response.status_code == 422


# ==============================
# Test Temperature Parameter
# ==============================
def test_chat_api_temperature():

    response = client.post(
        "/internal/llm/chat",
        json={
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "temperature": 0.5
        }
    )

    assert response.status_code == 200


# ==============================
# Test Max Tokens
# ==============================
def test_chat_api_max_tokens():

    response = client.post(
        "/internal/llm/chat",
        json={
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "max_tokens": 100
        }
    )

    assert response.status_code == 200


# ==============================
# Test Correlation ID
# ==============================
def test_chat_api_correlation_id():

    response = client.post(
        "/internal/llm/chat",
        json={
            "messages": [
                {"role": "user", "content": "Hello"}
            ],
            "correlation_id": "test123"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert "correlation_id" in data


# ==============================
# Test Response Structure
# ==============================
def test_chat_api_response_schema():

    response = client.post(
        "/internal/llm/chat",
        json={
            "messages": [
                {"role": "user", "content": "Hello"}
            ]
        }
    )

    data = response.json()

    assert "message" in data
    assert "provider" in data
    assert "model" in data
    assert "latency_ms" in data
    assert "tokens_used" in data