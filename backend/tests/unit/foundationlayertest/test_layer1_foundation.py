import pytest
import uuid
from unittest.mock import AsyncMock

from apps.foundation.core.llm_service import LLMService
from apps.foundation.providers.mock_adapter import MockProvider
from shared.schemas.chat import ChatRequest, ChatResponse, ChatMessage



# Test LLMService.chat

@pytest.mark.asyncio
async def test_llmservice_chat():

    mock_provider = MockProvider()

    mock_response = ChatResponse(
        message=ChatMessage(role="assistant", content="Hello from Mock"),
        provider="mock",
        model="mock-model",
        correlation_id=str(uuid.uuid4())
    )

    mock_provider.chat = AsyncMock(return_value=mock_response)

    service = LLMService(providers=[mock_provider])

    request = ChatRequest(
        messages=[
            {"role": "user", "content": "Say hi"}
        ],
        conversation_id="test123"
    )

    response = await service.chat(request)

    assert response is not None
    assert response.message.content == "Hello from Mock"



# Test Provider fallback

@pytest.mark.asyncio
async def test_provider_fallback():

    failing_provider = MockProvider()
    failing_provider.chat = AsyncMock(side_effect=Exception("Provider failed"))

    working_provider = MockProvider()

    mock_response = ChatResponse(
        message=ChatMessage(role="assistant", content="Fallback works"),
        provider="mock",
        model="mock-model",
        correlation_id=str(uuid.uuid4())
    )

    working_provider.chat = AsyncMock(return_value=mock_response)

    service = LLMService(providers=[failing_provider, working_provider])

    request = ChatRequest(
        messages=[
            {"role": "user", "content": "Hello"}
        ],
        conversation_id="abc"
    )

    response = await service.chat(request)

    assert response is not None
    assert response.message.content == "Fallback works"



# Test health API

from fastapi.testclient import TestClient
from apps.foundation.api.app import create_app


def test_health_endpoint():

    app = create_app()
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"