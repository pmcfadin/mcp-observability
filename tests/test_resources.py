import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_resources_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TOKEN", "testtoken")

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/resources", headers={"Authorization": "Bearer testtoken"})

    assert response.status_code == 200
    body = response.json()
    # New schema: {"resources": [...], "nextCursor": 1|null}
    assert "resources" in body
    assert body["resources"]
    first = body["resources"][0]
    assert "id" in first and "type" in first


@pytest.mark.asyncio
async def test_resources_list_pagination():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First page
        resp = await client.get("/resources?limit=1&cursor=0")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["resources"]) == 1
        next_cursor = data.get("nextCursor")
        assert next_cursor == 1 or next_cursor is None

        # Second page (if available)
        if next_cursor is not None:
            resp2 = await client.get(f"/resources?limit=1&cursor={next_cursor}")
            assert resp2.status_code == 200


@pytest.mark.asyncio
async def test_resource_read():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get first resource id
        list_resp = await client.get("/resources?limit=1")
        res_id = list_resp.json()["resources"][0]["id"]

        read_resp = await client.get(f"/resources/{res_id}")
        assert read_resp.status_code == 200
        assert read_resp.json()["id"] == res_id 