import pytest
from httpx import Response
from pytest_httpx import HTTPXMock

from app.clients import LokiClient


@pytest.mark.asyncio
async def test_search_logs(httpx_mock: HTTPXMock):
    fake_json = {"data": {"result": [{"values": [["1", "match"]]}]}}
    httpx_mock.add_response(
        url="http://loki:3100/loki/api/v1/query?query=%7B%7D+%7C%3D+%22match%22&limit=1000",
        json=fake_json,
    )

    client = LokiClient()
    logs = await client.search_logs("match", None, None)

    assert logs == ["match"]
