import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.routers.metrics import _execute_promql


class DummyResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


class DummyClient:
    """Minimal async context-manager mimicking httpx.AsyncClient."""

    def __init__(self, *, status_code: int = 200, json_data: dict | None = None):
        self._response = DummyResponse(status_code, json_data or {})

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str, params=None):
        return self._response


@pytest.mark.asyncio
async def test_execute_promql_success(monkeypatch: pytest.MonkeyPatch):
    fake_json = {
        "data": {
            "result": [
                {"metric": {"__name__": "up"}, "value": [1718486400, "1"]}
            ]
        }
    }

    monkeypatch.setattr(
        "app.routers.metrics.httpx.AsyncClient", lambda *a, **k: DummyClient(json_data=fake_json)
    )

    result = await _execute_promql("up")
    assert result == fake_json["data"]["result"]


@pytest.mark.asyncio
async def test_metrics_query_endpoint(monkeypatch: pytest.MonkeyPatch):
    fake_json = {
        "data": {
            "result": [
                {"metric": {"__name__": "up"}, "value": [1718486400, "1"]}
            ]
        }
    }

    monkeypatch.setenv("MCP_TOKEN", "testtoken")
    monkeypatch.setattr(
        "app.routers.metrics.httpx.AsyncClient", lambda *a, **k: DummyClient(json_data=fake_json)
    )

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/metrics/query",
            json={"query": "up"},
            headers={"Authorization": "Bearer testtoken"},
        )

    assert response.status_code == 200
    assert response.json() == {"result": fake_json["data"]["result"]} 