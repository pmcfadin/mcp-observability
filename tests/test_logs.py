import asyncio

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient, ConnectError, Response
from pytest_httpx import HTTPXMock

from app.clients import LokiClient
from app.main import app
from app.routers.logs import _fetch_error_logs

# Allow extra mocked responses that are not always consumed
pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


class DummyResponse:
    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json_data = json_data

    def json(self):
        return self._json_data


class DummyClient:
    """Minimal async context-manager mimicking httpx.AsyncClient."""

    def __init__(self, *, status_code: int = 200, json_data: dict | None = None):
        self._response = DummyResponse(status_code, json_data or {})

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False  # propagate exceptions

    async def get(self, url: str, params=None):
        # ignore url/params validation for brevity
        return self._response


@pytest.mark.asyncio
async def test_fetch_error_logs(httpx_mock: HTTPXMock):
    fake_json = {
        "data": {
            "result": [
                {
                    "values": [
                        ["1718486400000000", "first error"],
                        ["1718486400000001", "second error"],
                    ]
                }
            ]
        }
    }
    httpx_mock.add_response(json=fake_json)

    client = LokiClient()
    logs = await client.fetch_error_logs(10)

    assert logs == ["first error", "second error"]


@pytest.mark.asyncio
async def test_fetch_error_logs_loki_unavailable(httpx_mock: HTTPXMock):
    import httpx

    httpx_mock.add_exception(
        ConnectError("conn", request=httpx.Request("GET", "http://loki"))
    )

    client = LokiClient()
    with pytest.raises(HTTPException):
        await client.fetch_error_logs(10)


@pytest.mark.asyncio
async def test_fetch_error_logs_loki_error(httpx_mock: HTTPXMock):
    httpx_mock.add_response(status_code=500, is_optional=True)

    client = LokiClient()
    with pytest.raises(HTTPException):
        await client.fetch_error_logs(10)


@pytest.mark.asyncio
async def test_fetch_error_logs_invalid_payload(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"data": {"invalid": "payload"}}, is_optional=True)

    client = LokiClient()
    with pytest.raises(HTTPException):
        await client.fetch_error_logs(10)


@pytest.mark.asyncio
async def test_fetch_error_logs_no_logs(httpx_mock: HTTPXMock):
    httpx_mock.add_response(json={"data": {"result": []}}, is_optional=True)

    client = LokiClient()
    logs = await client.fetch_error_logs(10)

    assert logs == []


@pytest.mark.asyncio
async def test_logs_errors_endpoint(monkeypatch: pytest.MonkeyPatch):
    """Endpoint returns logs array when provided valid token."""

    class MockLokiClient:
        async def fetch_error_logs(
            self, limit: int, service: str | None = None, time_range: str | None = None
        ):
            return ["err one", "err two"]

    app.dependency_overrides[LokiClient] = MockLokiClient
    monkeypatch.setenv("MCP_TOKEN", "testtoken")

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/logs/errors?limit=2",
            headers={"Authorization": "Bearer testtoken"},
        )

    assert response.status_code == 200
    assert response.json() == {"logs": ["err one", "err two"]}

    del app.dependency_overrides[LokiClient]
