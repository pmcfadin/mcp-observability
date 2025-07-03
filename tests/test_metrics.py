import pytest
from httpx import ASGITransport, AsyncClient, Response
from pytest_httpx import HTTPXMock

from app.clients import PrometheusClient
from app.config import get_settings
from app.main import app

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


@pytest.mark.asyncio
async def test_metrics_latency_endpoint(monkeypatch: pytest.MonkeyPatch):
    class MockPrometheusClient:
        async def fetch_latency_percentile(
            self, percentile: float, time_range: str, service: str | None = None
        ):
            return 0.456

    app.dependency_overrides[PrometheusClient] = MockPrometheusClient
    monkeypatch.setenv("MCP_TOKEN", "testtoken")
    get_settings.cache_clear()

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/metrics/latency?percentile=0.95&time_range=5m",
            headers={"Authorization": "Bearer testtoken"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "percentile": 0.95,
        "time_range": "5m",
        "latency_seconds": 0.456,
    }

    del app.dependency_overrides[PrometheusClient]


@pytest.mark.asyncio
async def test_fetch_latency_percentile(httpx_mock: HTTPXMock):
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
    httpx_mock.add_response(
        url="http://prometheus:9090/api/v1/query?query=histogram_quantile%280.95%2C+sum%28rate%28http_server_request_duration_seconds_bucket%5B5m%5D%29%29+by+%28le%29%29",
        json=fake_json,
    )

    client = PrometheusClient()
    latency = await client.fetch_latency_percentile(0.95, "5m")

    assert pytest.approx(latency, rel=1e-6) == 0.123
