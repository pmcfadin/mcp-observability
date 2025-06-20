import pytest
from httpx import AsyncClient, ASGITransport

from app.clients import PrometheusClient
from app.main import app


@pytest.mark.asyncio
async def test_metrics_query_endpoint(monkeypatch: pytest.MonkeyPatch):
    fake_result = [{"metric": {"__name__": "up"}, "value": [1718486400, "1"]}]

    class MockPrometheusClient:
        async def execute_promql(self, promql: str):
            return fake_result

    app.dependency_overrides[PrometheusClient] = MockPrometheusClient
    monkeypatch.setenv("MCP_TOKEN", "testtoken")

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/metrics/query",
            json={"query": "up"},
            headers={"Authorization": "Bearer testtoken"},
        )

    assert response.status_code == 200
    assert response.json() == {"result": fake_result}

    del app.dependency_overrides[PrometheusClient] 