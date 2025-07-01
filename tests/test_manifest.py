import pytest
from httpx import ASGITransport, AsyncClient

from app.initialize import SUPPORTED_VERSION
from app.main import app


@pytest.mark.asyncio
async def test_manifest():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/manifest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["version"] == SUPPORTED_VERSION
        assert "resources" in data and isinstance(data["resources"], list)
        assert "prompts" in data and isinstance(data["prompts"], list)
