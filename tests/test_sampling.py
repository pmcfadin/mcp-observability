import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from mcp_observability.schemas import (
    Message,
    MessageContent,
    MessageContentType,
    MessageRole,
    SamplingRequest,
)


@pytest.mark.asyncio
async def test_sampling_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MCP_TOKEN", "testtoken")

    request_payload = SamplingRequest(
        messages=[
            Message(
                role=MessageRole.user,
                content=MessageContent(type=MessageContentType.text, text="hello"),
            )
        ],
        maxTokens=16,
    )

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post(
            "/sampling",
            json=request_payload.model_dump(by_alias=True),
            headers={"Authorization": "Bearer testtoken"},
        )

    assert response.status_code == 200
    data = response.json()
    # We expect echoed uppercase text
    assert data["content"]["text"] == "HELLO"


@pytest.mark.asyncio
async def test_sampling_echo():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        req = {
            "messages": [
                {
                    "role": "user",
                    "content": {"type": "text", "text": "hello"},
                }
            ],
            "maxTokens": 5,
        }
        resp = await client.post("/sampling", json=req)
        assert resp.status_code == 200
        assert resp.json()["content"]["text"] == "HELLO"
