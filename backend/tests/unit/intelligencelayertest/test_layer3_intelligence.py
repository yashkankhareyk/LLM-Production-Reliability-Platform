from fastapi.testclient import TestClient
from apps.intelligence.main import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "message": "Intelligence layer is running"
    }