import pytest
from httpx import ASGITransport, AsyncClient, Response
from pytest_httpx import HTTPXMock

from app.clients import LokiClient, TempoClient
from app.main import app

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


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
    from app.config import get_settings

    get_settings.cache_clear()

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
    httpx_mock.add_response(json=fake_trace, is_optional=True)

    client = TempoClient()
    trace = await client.fetch_trace_json("abc")

    assert trace == fake_trace


@pytest.mark.asyncio
async def test_fetch_trace_logs(httpx_mock: HTTPXMock):
    fake_json = {"data": {"result": [{"values": [["1", "log1"], ["2", "log2"]]}]}}
    httpx_mock.add_response(json=fake_json, is_optional=True)

    client = LokiClient()
    logs = await client.fetch_trace_logs("abc", 10)

    assert logs == ["log1", "log2"]
