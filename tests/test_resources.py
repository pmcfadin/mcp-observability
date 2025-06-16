import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_resources_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TOKEN", "testtoken")

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(
            "/resources", headers={"Authorization": "Bearer testtoken"}
        )

    assert response.status_code == 200
    body = response.json()
    # Expect at least one resource with required keys
    assert isinstance(body, list)
    assert body and "id" in body[0]
    assert body[0]["type"] == "text" 