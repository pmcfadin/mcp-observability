from __future__ import annotations

import os
from typing import Any, Optional, cast

from fastapi import APIRouter, HTTPException, status

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

# Lazy optional OpenAI client
try:
    import openai  # type: ignore

    _openai_available = True
except ModuleNotFoundError:  # pragma: no cover
    _openai_available = False

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

# OpenAI config via env vars
_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
_OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")


@router.post(
    "/sampling", response_model=SamplingResponse, status_code=status.HTTP_200_OK
)
async def sampling_endpoint(request: SamplingRequest) -> SamplingResponse:
    """Proxy a sampling request to an upstream client or echo back.

    Flow:
    1. If MCP python SDK is available **and** MCP_SAMPLER_URL is set, forward
       the request via HTTP to that sampler endpoint (blocking call).
    2. Else if OpenAI is available and OPENAI_API_KEY is set, use OpenAI as a fallback.
    3. Else fall back to local echo implementation identical to previous MVP.
    """

    if _SamplerClient and _SAMPLER_ENDPOINT:
        try:
            client = _SamplerClient(_SAMPLER_ENDPOINT)
            rst = client.sample(request.model_dump(by_alias=True))
            # Assume rst already matches SamplingResponse schema.
            return SamplingResponse(**rst)
        except Exception as exc:  # pragma: no cover – network failure path
            raise HTTPException(
                status_code=502, detail=f"Sampler proxy error: {exc}"
            ) from exc

    # 3. OpenAI fallback if credentials provided ---------------------------------------
    if _openai_available and _OPENAI_API_KEY:
        try:
            openai.api_key = _OPENAI_API_KEY  # type: ignore[attr-defined]

            # Convert MCP messages → OpenAI format
            oa_messages = [
                {"role": m.role.value, "content": m.content.text}
                for m in request.messages
                if m.content.text is not None
            ]

            # Include optional system prompt at beginning
            if request.system_prompt:
                oa_messages.insert(
                    0, {"role": "system", "content": request.system_prompt}
                )

            rsp = openai.chat.completions.create(  # type: ignore[attr-defined]
                model=_OPENAI_MODEL,
                messages=cast(Any, oa_messages),
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens,
                stop=request.stop_sequences,
            )

            choice = rsp.choices[0]
            return SamplingResponse(
                model=choice.model or _OPENAI_MODEL,  # type: ignore[attr-defined]
                role=MessageRole.assistant,
                content=MessageContent(type=MessageContentType.text, text=choice.message.content),  # type: ignore[attr-defined]
                stop_reason=choice.finish_reason,
            )
        except Exception as exc:  # pragma: no cover – network/credential errors
            raise HTTPException(
                status_code=502, detail=f"OpenAI proxy error: {exc}"
            ) from exc

    # --- Fallback: local echo ---------------------------
    first_user_msg = next(
        (m for m in request.messages if m.role == MessageRole.user), None
    )
    if isinstance(first_user_msg, Message) and first_user_msg.content.text:
        reply_text = first_user_msg.content.text.upper()
    else:
        reply_text = "OK"

    return SamplingResponse(
        model="mock",
        role=MessageRole.assistant,
        content=MessageContent(type=MessageContentType.text, text=reply_text),
        stop_reason="endTurn",
    )
