import asyncio

import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app, _fetch_error_logs


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
async def test_fetch_error_logs_success(monkeypatch: pytest.MonkeyPatch):
    """Helper should return parsed log lines from Loki JSON payload."""

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

    monkeypatch.setattr("app.main.httpx.AsyncClient", lambda *a, **k: DummyClient(json_data=fake_json))

    lines = await _fetch_error_logs(10)
    assert lines == ["first error", "second error"]


@pytest.mark.asyncio
async def test_logs_errors_endpoint(monkeypatch: pytest.MonkeyPatch):
    """Endpoint returns logs array when provided valid token."""

    fake_json = {
        "data": {
            "result": [
                {"values": [["123", "err one"], ["124", "err two"]]}
            ]
        }
    }

    monkeypatch.setenv("MCP_TOKEN", "testtoken")
    monkeypatch.setattr("app.main.httpx.AsyncClient", lambda *a, **k: DummyClient(json_data=fake_json))

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/logs/errors?limit=2",
            headers={"Authorization": "Bearer testtoken"},
        )

    assert response.status_code == 200
    assert response.json() == {"logs": ["err one", "err two"]} 