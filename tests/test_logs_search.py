import pytest
from httpx import ASGITransport, AsyncClient

from app.main import _search_logs, app


class DummyResponse:
    def __init__(self, json_data):
        self.status_code = 200
        self._json = json_data

    def json(self):
        return self._json


class DummyClient:
    def __init__(self, json_data):
        self._resp = DummyResponse(json_data)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, url, params=None):
        return self._resp


@pytest.mark.asyncio
async def test_search_logs_helper(monkeypatch: pytest.MonkeyPatch):
    fake = {"data": {"result": [{"values": [["1", "found"]]}]}}
    monkeypatch.setattr("app.main.httpx.AsyncClient", lambda *a, **k: DummyClient(fake))

    lines = await _search_logs("error", None, "1h")
    assert lines == ["found"]


@pytest.mark.asyncio
async def test_search_logs_endpoint(monkeypatch: pytest.MonkeyPatch):
    fake = {"data": {"result": [{"values": [["1", "match"]]}]}}
    monkeypatch.setattr("app.main.httpx.AsyncClient", lambda *a, **k: DummyClient(fake))
    monkeypatch.setenv("MCP_TOKEN", "tok")

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/logs/search",
            json={"query": "match"},
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.status_code == 200
    assert resp.json() == {"logs": ["match"]}
