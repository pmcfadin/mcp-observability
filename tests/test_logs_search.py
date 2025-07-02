import httpx
import pytest
from fastapi import HTTPException
from httpx import ConnectError, Response
from pytest_httpx import HTTPXMock

from app.clients import LokiClient

# Allow unused mocked responses in this module
pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


@pytest.mark.asyncio
async def test_search_logs(httpx_mock: HTTPXMock):
    fake_json = {"data": {"result": [{"values": [["1", "match"]]}]}}
    httpx_mock.add_response(json=fake_json)

    client = LokiClient()
    logs = await client.search_logs("match", None, None)

    assert logs == ["match"]


@pytest.mark.asyncio
async def test_search_logs_loki_unavailable(httpx_mock: HTTPXMock):
    httpx_mock.add_exception(
        ConnectError("conn", request=httpx.Request("GET", "http://loki"))
    )

    client = LokiClient()
    with pytest.raises(HTTPException):
        await client.search_logs("match", None, None)


@pytest.mark.asyncio
async def test_search_logs_loki_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=500)

    client = LokiClient()
    with pytest.raises(Exception):
        await client.search_logs("match", None, None)


@pytest.mark.asyncio
async def test_search_logs_invalid_payload(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"data": {"invalid": "payload"}}, is_optional=True)

    client = LokiClient()
    with pytest.raises(Exception):
        await client.search_logs("match", None, None)


@pytest.mark.asyncio
async def test_search_logs_no_logs(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"data": {"result": []}}, is_optional=True)

    client = LokiClient()
    logs = await client.search_logs("match", None, None)

    assert logs == []
