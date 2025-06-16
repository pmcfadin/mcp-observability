from __future__ import annotations

import os
from typing import Optional, Any

from fastapi import APIRouter, status, HTTPException

from mcp_observability.schemas import (
    Message,
    MessageContent,
    MessageContentType,
    MessageRole,
    SamplingRequest,
    SamplingResponse,
)

router = APIRouter(tags=["mcp"])

# Try importing the (optional) MCP python SDK.  The package name may evolve –
# we attempt multiple known aliases so that the code remains functional even
# when the dependency is absent (CI fallback mode).
_SamplerClient: Any | None = None  # noqa: UP007 (py3.9 compatibility)

for _pkg in ("modelcontextprotocol", "mcp_sdk", "mcp"):
    try:
        from importlib import import_module

        _mod = import_module(f"{_pkg}.client")
        _SamplerClient = getattr(_mod, "SamplerClient", None)
        if _SamplerClient is not None:
            break
    except ModuleNotFoundError:
        continue

_SAMPLER_ENDPOINT = os.getenv("MCP_SAMPLER_URL")


@router.post("/sampling", response_model=SamplingResponse, status_code=status.HTTP_200_OK)
async def sampling_endpoint(request: SamplingRequest) -> SamplingResponse:
    """Proxy a sampling request to an upstream client or echo back.

    Flow:
    1. If MCP python SDK is available **and** MCP_SAMPLER_URL is set, forward
       the request via HTTP to that sampler endpoint (blocking call).
    2. Else fall back to local echo implementation identical to previous MVP.
    """

    if _SamplerClient and _SAMPLER_ENDPOINT:
        try:
            client = _SamplerClient(_SAMPLER_ENDPOINT)
            rst = client.sample(request.model_dump(by_alias=True))
            # Assume rst already matches SamplingResponse schema.
            return SamplingResponse(**rst)
        except Exception as exc:  # pragma: no cover – network failure path
            raise HTTPException(status_code=502, detail=f"Sampler proxy error: {exc}") from exc

    # --- Fallback: local echo ---------------------------
    first_user_msg = next((m for m in request.messages if m.role == MessageRole.user), None)
    reply_text = first_user_msg.content.text.upper() if isinstance(first_user_msg, Message) else "OK"

    return SamplingResponse(
        model="mock",
        role=MessageRole.assistant,
        content=MessageContent(type=MessageContentType.text, text=reply_text),
        stop_reason="endTurn",
    ) 