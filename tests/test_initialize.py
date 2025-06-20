import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_initialize_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/initialize",
            json={
                "version": "2024-11-05",
                "client": {"name": "test-client", "version": "0.0.1"},
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["version"] == "2024-11-05"
        assert data["capabilities"]["resources"] is True


@pytest.mark.asyncio
async def test_initialize_version_mismatch():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/initialize",
            json={
                "version": "2023-01-01",  # unsupported
                "client": {"name": "test-client"},
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        # Server responds with supported version
        assert data["version"] == "2024-11-05"
