import pytest
from httpx import ASGITransport, AsyncClient

from app.main import _fetch_trace_json, _fetch_trace_logs, app


class DummyResponse:
    def __init__(self, status_code: int = 200, json_data=None):
        self.status_code = status_code
        self._json = json_data or {}

    def json(self):
        return self._json


class DummyClient:
    def __init__(self, *, status_code: int = 200, json_data=None):
        self._resp = DummyResponse(status_code, json_data)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, *a, **kw):
        return self._resp


@pytest.mark.asyncio
async def test_fetch_trace_json(monkeypatch: pytest.MonkeyPatch):
    fake = {"data": {"traceID": "abc"}}
    monkeypatch.setattr(
        "app.main.httpx.AsyncClient", lambda *a, **k: DummyClient(json_data=fake)
    )

    result = await _fetch_trace_json("abc")
    assert result == fake


@pytest.mark.asyncio
async def test_fetch_trace_logs(monkeypatch: pytest.MonkeyPatch):
    fake = {"data": {"result": [{"values": [["1", "log1"], ["2", "log2"]]}]}}
    monkeypatch.setattr(
        "app.main.httpx.AsyncClient", lambda *a, **k: DummyClient(json_data=fake)
    )

    logs = await _fetch_trace_logs("abc", 10)
    assert logs == ["log1", "log2"]


@pytest.mark.asyncio
async def test_trace_endpoints(monkeypatch: pytest.MonkeyPatch):
    fake_trace = {"data": {"traceID": "abc"}}
    fake_logs = {"data": {"result": [{"values": [["1", "l1"]]}]}}

    monkeypatch.setenv("MCP_TOKEN", "tok")

    # Patch helper functions instead of HTTP layer for simplicity
    async def fake_json(trace_id):
        return fake_trace

    async def fake_logs(trace_id, limit):
        return ["l1"]

    monkeypatch.setattr("app.main._fetch_trace_json", fake_json)
    monkeypatch.setattr("app.main._fetch_trace_logs", fake_logs)

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        trace = await ac.get("/traces/abc", headers={"Authorization": "Bearer tok"})
        assert trace.status_code == 200
        assert trace.json() == fake_trace

        logs = await ac.get("/traces/abc/logs", headers={"Authorization": "Bearer tok"})
        assert logs.status_code == 200
        assert logs.json() == {"logs": ["l1"]}
