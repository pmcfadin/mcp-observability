import pytest
from httpx import Response, ConnectError
from pytest_httpx import HTTPXMock

from app.clients import PrometheusClient


@pytest.mark.asyncio
async def test_execute_promql(httpx_mock: HTTPXMock):
    fake_json = {
        "data": {
            "result": [
                {"metric": {"__name__": "up"}, "value": [1718486400, "1"]}
            ]
        }
    }
    httpx_mock.add_response(
        url="http://prometheus:9090/api/v1/query?query=up",
        json=fake_json,
    )

    client = PrometheusClient()
    result = await client.execute_promql("up")

    assert result == fake_json["data"]["result"]


@pytest.mark.asyncio
async def test_execute_promql_prometheus_unavailable(httpx_mock: HTTPXMock):
    httpx_mock.add_exception(ConnectError())

    client = PrometheusClient()
    with pytest.raises(ConnectError):
        await client.execute_promql("up")


@pytest.mark.asyncio
async def test_execute_promql_prometheus_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=500)

    client = PrometheusClient()
    with pytest.raises(Exception):
        await client.execute_promql("up")


@pytest.mark.asyncio
async def test_execute_promql_invalid_payload(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"data": {"invalid": "payload"}})

    client = PrometheusClient()
    with pytest.raises(Exception):
        await client.execute_promql("up")


@pytest.mark.asyncio
async def test_execute_promql_empty_result(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"data": {"result": []}})

    client = PrometheusClient()
    result = await client.execute_promql("up")

    assert result == []
