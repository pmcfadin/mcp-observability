import pytest
from httpx import ConnectError, Response
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


@pytest.mark.asyncio
async def test_search_logs_loki_unavailable(httpx_mock: HTTPXMock):
    httpx_mock.add_exception(ConnectError())

    client = LokiClient()
    with pytest.raises(ConnectError):
        await client.search_logs("match", None, None)


@pytest.mark.asyncio
async def test_search_logs_loki_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=500)

    client = LokiClient()
    with pytest.raises(Exception):
        await client.search_logs("match", None, None)


@pytest.mark.asyncio
async def test_search_logs_invalid_payload(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"data": {"invalid": "payload"}})

    client = LokiClient()
    with pytest.raises(Exception):
        await client.search_logs("match", None, None)


@pytest.mark.asyncio
async def test_search_logs_no_logs(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"data": {"result": []}})

    client = LokiClient()
    logs = await client.search_logs("match", None, None)

    assert logs == []
