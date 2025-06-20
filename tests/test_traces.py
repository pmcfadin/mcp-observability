import pytest
from httpx import ASGITransport, AsyncClient, Response
from pytest_httpx import HTTPXMock

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

        logs_resp = await ac.get(
            "/traces/abc/logs", headers={"Authorization": "Bearer tok"}
        )
        assert logs_resp.status_code == 200
        assert logs_resp.json() == {"logs": ["l1"]}

    del app.dependency_overrides[TempoClient]
    del app.dependency_overrides[LokiClient]


@pytest.mark.asyncio
async def test_fetch_trace_json(httpx_mock: HTTPXMock):
    fake_trace = {"data": {"traceID": "abc"}}
    httpx_mock.add_response(
        url="http://tempo:3200/api/traces/abc",
        json=fake_trace,
    )

    client = TempoClient()
    trace = await client.fetch_trace_json("abc")

    assert trace == fake_trace


@pytest.mark.asyncio
async def test_fetch_trace_logs(httpx_mock: HTTPXMock):
    fake_json = {"data": {"result": [{"values": [["1", "log1"], ["2", "log2"]]}]}}
    httpx_mock.add_response(
        url="http://loki:3100/loki/api/v1/query?query=%7Btrace_id%3D%22abc%22%7D&limit=10",
        json=fake_json,
    )

    client = LokiClient()
    logs = await client.fetch_trace_logs("abc", 10)

    assert logs == ["log1", "log2"]
