import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app, _fetch_active_alerts


class DummyResponse:
    def __init__(self, status_code: int, json_data):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


class DummyClient:
    def __init__(self, *, status_code=200, json_data=None):
        self._response = DummyResponse(status_code, json_data or [])

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url: str):
        return self._response


@pytest.mark.asyncio
async def test_fetch_active_alerts_filters(monkeypatch: pytest.MonkeyPatch):
    alerts_json = [
        {"labels": {"alertname": "HighCPU", "severity": "critical", "service": "api"}},
        {"labels": {"alertname": "HighMem", "severity": "warning", "service": "worker"}},
    ]

    monkeypatch.setattr("app.main.httpx.AsyncClient", lambda *a, **k: DummyClient(json_data=alerts_json))

    filtered = await _fetch_active_alerts(severity="critical", service="api")
    assert filtered == [alerts_json[0]]


@pytest.mark.asyncio
async def test_alerts_endpoint(monkeypatch: pytest.MonkeyPatch):
    alerts_json = [
        {"labels": {"alertname": "HighCPU", "severity": "critical", "service": "api"}}
    ]

    monkeypatch.setenv("MCP_TOKEN", "testtoken")
    monkeypatch.setattr("app.main.httpx.AsyncClient", lambda *a, **k: DummyClient(json_data=alerts_json))

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/alerts?severity=critical&service=api",
            headers={"Authorization": "Bearer testtoken"},
        )

    assert resp.status_code == 200
    assert resp.json() == {"alerts": alerts_json} 