import pytest
from httpx import ASGITransport, AsyncClient, Response, ConnectError
from pytest_httpx import HTTPXMock

from app.clients import PrometheusClient
from app.main import app


@pytest.mark.asyncio
async def test_metrics_latency_endpoint(monkeypatch: pytest.MonkeyPatch):
    class MockPrometheusClient:
        async def fetch_latency_percentile(
            self, percentile: float, time_range: str, service: str | None = None
        ):
            return 0.456

    app.dependency_overrides[PrometheusClient] = MockPrometheusClient
    monkeypatch.setenv("MCP_TOKEN", "testtoken")

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


@pytest.mark.asyncio
async def test_fetch_latency_percentile_prometheus_unavailable(httpx_mock: HTTPXMock):
    httpx_mock.add_exception(ConnectError())

    client = PrometheusClient()
    with pytest.raises(ConnectError):
        await client.fetch_latency_percentile(0.95, "5m")


@pytest.mark.asyncio
async def test_fetch_latency_percentile_prometheus_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=500)

    client = PrometheusClient()
    with pytest.raises(Exception):
        await client.fetch_latency_percentile(0.95, "5m")


@pytest.mark.asyncio
async def test_fetch_latency_percentile_invalid_payload(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"data": {"invalid": "payload"}})

    client = PrometheusClient()
    with pytest.raises(Exception):
        await client.fetch_latency_percentile(0.95, "5m")


@pytest.mark.asyncio
async def test_fetch_latency_percentile_non_numeric(httpx_mock: HTTPXMock):
    fake_json = {
        "data": {
            "result": [
                {
                    "value": [
                        1718486400,
                        "not-a-number",
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
    with pytest.raises(Exception):
        await client.fetch_latency_percentile(0.95, "5m")


@pytest.mark.asyncio
async def test_fetch_latency_percentile_empty_result(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"data": {"result": []}})

    client = PrometheusClient()
    with pytest.raises(Exception):
        await client.fetch_latency_percentile(0.95, "5m")
