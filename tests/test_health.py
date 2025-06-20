import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    """Endpoint should return 200 when a valid bearer token is provided."""

    monkeypatch.setenv("MCP_TOKEN", "testtoken")

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/health",
            headers={"Authorization": "Bearer testtoken"},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
