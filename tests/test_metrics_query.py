import pytest
from httpx import Response
from pytest_httpx import HTTPXMock

from app.clients import PrometheusClient


@pytest.mark.asyncio
async def test_execute_promql(httpx_mock: HTTPXMock):
    fake_json = {
        "data": {"result": [{"metric": {"__name__": "up"}, "value": [1718486400, "1"]}]}
    }
    httpx_mock.add_response(
        url="http://prometheus:9090/api/v1/query?query=up",
        json=fake_json,
    )

    client = PrometheusClient()
    result = await client.execute_promql("up")

    assert result == fake_json["data"]["result"]
