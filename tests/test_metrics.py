import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app, _fetch_latency_percentile


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
async def test_fetch_latency_success(monkeypatch: pytest.MonkeyPatch):
    fake_json = {
        "data": {
            "result": [
                {
                    "value": [
                        1718486400,
                        "0.123",
                    ]
                }
            ]
        }
    }

    monkeypatch.setattr("app.main.httpx.AsyncClient", lambda *a, **k: DummyClient(json_data=fake_json))

    latency = await _fetch_latency_percentile(0.95, "5m")
    assert pytest.approx(latency, rel=1e-6) == 0.123


@pytest.mark.asyncio
async def test_metrics_latency_endpoint(monkeypatch: pytest.MonkeyPatch):
    fake_json = {
        "data": {
            "result": [
                {"value": [1718486400, "0.456"]}
            ]
        }
    }

    monkeypatch.setenv("MCP_TOKEN", "testtoken")
    monkeypatch.setattr("app.main.httpx.AsyncClient", lambda *a, **k: DummyClient(json_data=fake_json))

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/metrics/latency?percentile=0.95&window=5m",
            headers={"Authorization": "Bearer testtoken"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "percentile": 0.95,
        "window": "5m",
        "latency_seconds": 0.456,
    } 