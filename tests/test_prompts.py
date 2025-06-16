import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_prompts_list():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/prompts")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list) and len(data) >= 1
        assert any(p["id"] == "greet" for p in data)


@pytest.mark.asyncio
async def test_prompt_render():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/prompts/greet/render", json={"name": "Alice"})
        assert resp.status_code == 200
        assert resp.json()["prompt"].startswith("Hello, Alice") 