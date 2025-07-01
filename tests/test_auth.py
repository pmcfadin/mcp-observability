import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_unauthorized_when_header_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Request without Authorization header should be rejected with 401."""

    monkeypatch.setenv("MCP_TOKEN", "secret")

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthorized_when_token_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mismatched bearer token should also be rejected."""

    monkeypatch.setenv("MCP_TOKEN", "secret")

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/health",
            headers={"Authorization": "Bearer wrongtoken"},
        )

    assert response.status_code == 401
