import pytest
from httpx import ASGITransport, AsyncClient

from app.clients import LokiClient
from app.main import app


@pytest.mark.asyncio
async def test_search_logs_endpoint(monkeypatch: pytest.MonkeyPatch):
    class MockLokiClient:
        async def search_logs(
            self, query: str, service: str | None, time_range: str | None
        ):
            return ["match"]

    app.dependency_overrides[LokiClient] = MockLokiClient
    monkeypatch.setenv("MCP_TOKEN", "tok")

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/logs/search",
            json={"query": "match"},
            headers={"Authorization": "Bearer tok"},
        )

    assert resp.status_code == 200
    assert resp.json() == {"logs": ["match"]}

    del app.dependency_overrides[LokiClient]
