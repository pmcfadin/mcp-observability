from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from mcp_observability.schemas import (
    InitializeRequest,
    InitializeResponse,
    Capabilities,
    ServerInfo,
)

router = APIRouter(tags=["mcp"], prefix="")  # keep root-level path

SUPPORTED_VERSION = "2024-11-05"


@router.post("/initialize", response_model=InitializeResponse, status_code=status.HTTP_200_OK)
async def initialize(request: InitializeRequest) -> InitializeResponse:  # noqa: D401
    """MCP lifecycle `initialize` handshake (partial spec).

    The server currently supports exactly one protocol revision (2024-11-05).
    If the client requests another version we respond with *our* supported
    version so the client can decide whether to continue.  This mirrors the
    negotiation behaviour defined in the spec.
    """

    if request.version != SUPPORTED_VERSION:
        # The spec says: respond with latest version we *do* support. Clients
        # may disconnect if they cannot handle it. We do *not* treat this as
        # an error status-code wise.
        responded_version = SUPPORTED_VERSION
    else:
        responded_version = request.version

    # Figure out advertised capabilities based on implemented routers
    server_caps = Capabilities(
        resources=True,
        prompts=True,
        tools=True,
        sampling=True,
    )

    return InitializeResponse(
        version=responded_version,
        server=ServerInfo(name="mcp-observability", version="0.1.0"),
        capabilities=server_caps,
    ) 