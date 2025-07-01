import pytest
from httpx import AsyncClient, ASGITransport

from app.clients import PrometheusClient
from app.main import app


@pytest.mark.asyncio
async def test_metrics_latency_endpoint(monkeypatch: pytest.MonkeyPatch):
    class MockPrometheusClient:
        async def fetch_latency_percentile(
            self, percentile: float, window: str, service: str | None = None
        ):
            return 0.456

    app.dependency_overrides[PrometheusClient] = MockPrometheusClient
    monkeypatch.setenv("MCP_TOKEN", "testtoken")

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

    del app.dependency_overrides[PrometheusClient] 