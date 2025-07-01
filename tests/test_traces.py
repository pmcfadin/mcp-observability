import pytest
from httpx import ASGITransport, AsyncClient

from app.clients import LokiClient, TempoClient
from app.main import app


@pytest.mark.asyncio
async def test_trace_endpoints(monkeypatch: pytest.MonkeyPatch):
    fake_trace = {"data": {"traceID": "abc"}}

    class MockTempoClient:
        async def fetch_trace_json(self, trace_id: str):
            return fake_trace

    class MockLokiClient:
        async def fetch_trace_logs(self, trace_id: str, limit: int):
            return ["l1"]

    app.dependency_overrides[TempoClient] = MockTempoClient
    app.dependency_overrides[LokiClient] = MockLokiClient
    monkeypatch.setenv("MCP_TOKEN", "tok")

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        trace = await ac.get("/traces/abc", headers={"Authorization": "Bearer tok"})
        assert trace.status_code == 200
        assert trace.json() == fake_trace

        logs_resp = await ac.get("/traces/abc/logs", headers={"Authorization": "Bearer tok"})
        assert logs_resp.status_code == 200
        assert logs_resp.json() == {"logs": ["l1"]}

    del app.dependency_overrides[TempoClient]
    del app.dependency_overrides[LokiClient]
