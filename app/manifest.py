from __future__ import annotations

"""Manifest endpoint returns a summary of server capabilities & content."""

from fastapi import APIRouter, status

from mcp_observability.schemas import Manifest, Capabilities

from app.initialize import SUPPORTED_VERSION
from app.resource_store import list_resources
from app.prompt_store import list_prompts

# Attempt to collect tool names from FastMCP registry (best-effort)
try:
    from app.mcp_server import mcp as _mcp

    _TOOL_NAMES = [t.__name__ for t in _mcp._tools]  # pyright: ignore[reportPrivateUsage]
except Exception:  # pragma: no cover
    _TOOL_NAMES = []

router = APIRouter(tags=["mcp"], prefix="")


def _current_capabilities() -> Capabilities:
    return Capabilities(resources=True, prompts=True, tools=True, sampling=True)


@router.get("/manifest", response_model=Manifest, status_code=status.HTTP_200_OK)
async def manifest() -> Manifest:  # noqa: D401
    return Manifest(
        version=SUPPORTED_VERSION,
        capabilities=_current_capabilities(),
        resources=[r.id for r in list_resources()],
        prompts=[p.id for p in list_prompts()],
        tools=_TOOL_NAMES or None,
    ) 