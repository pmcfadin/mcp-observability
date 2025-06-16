from __future__ import annotations

from fastapi import APIRouter, status

from mcp_observability.schemas import (
    Message,
    MessageContent,
    MessageContentType,
    MessageRole,
    SamplingRequest,
    SamplingResponse,
)

router = APIRouter(tags=["mcp"])


@router.post("/sampling", response_model=SamplingResponse, status_code=status.HTTP_200_OK)
async def sampling_endpoint(request: SamplingRequest) -> SamplingResponse:
    """Proxy a sampling request.

    In a full MCP implementation this endpoint would forward the request to the
    connected client for LLM completion.  For the MVP we echo back a dummy
    response so that the contract and wiring can be validated by automated
    tests and example clients.
    """

    # Simple echo: respond with first user message upper-cased
    first_user_msg = next((m for m in request.messages if m.role == MessageRole.user), None)
    reply_text = first_user_msg.content.text.upper() if isinstance(first_user_msg, Message) else "OK"

    return SamplingResponse(
        model="mock",
        role=MessageRole.assistant,
        content=MessageContent(type=MessageContentType.text, text=reply_text),
        stop_reason="endTurn",
    ) 