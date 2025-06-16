import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_prompts_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TOKEN", "testtoken")

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/prompts", headers={"Authorization": "Bearer testtoken"}
        )

    assert response.status_code == 200
    data = response.json()
    assert data and data[0]["id"] == "greet" 