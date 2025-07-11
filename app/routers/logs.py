from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.clients import LokiClient
from app.security import verify_bearer_token

router = APIRouter(
    prefix="/logs",
    tags=["logs"],
    dependencies=[Depends(verify_bearer_token)],
)


@router.get(
    "/errors",
    status_code=status.HTTP_200_OK,
)
async def logs_errors(
    limit: int = Query(100, ge=1, le=1000),
    service: str | None = Query(None, pattern=r"^[a-zA-Z0-9_-]+$"),
    range: str | None = Query(None, pattern=r"^\d+[smhd]$"),
    client: LokiClient = Depends(LokiClient),
) -> dict[str, list[str]]:
    """Return the last *limit* error log lines from Loki.

    The endpoint proxies a query to the Loki HTTP API, returning only the raw
    log lines so that API consumers do not need to know Loki's schema.
    """

    logs = await client.fetch_error_logs(limit, service, range)
    return {"logs": logs}


class LogSearchRequest(BaseModel):
    query: str
    service: str | None = None
    range: str | None = "1h"


@router.post(
    "/search",
    status_code=status.HTTP_200_OK,
)
async def logs_search(
    request: LogSearchRequest, client: LokiClient = Depends(LokiClient)
) -> dict[str, list[str]]:
    """Return log lines matching query (and optional service) from Loki."""

    logs = await client.search_logs(request.query, request.service, request.range)
    return {"logs": logs}


# ---------------------------------------------------------------------------
# Internal helper wrappers used by tests -------------------------------------
# ---------------------------------------------------------------------------


async def _fetch_error_logs(
    limit: int = 100,
    service: str | None = None,
    time_range: str | None = None,
) -> list[str]:
    """Convenience wrapper so unit-tests can call Loki fetch directly.

    It instantiates a `LokiClient` with default settings and delegates to the
    real implementation.  Not used by production endpoints but kept to avoid
    breaking existing tests.
    """

    client = LokiClient()
    return await client.fetch_error_logs(limit, service, time_range)


async def _search_logs(
    query: str,
    service: str | None = None,
    time_range: str | None = None,
) -> list[str]:
    """Wrapper for unit tests to call `LokiClient.search_logs`."""

    client = LokiClient()
    return await client.search_logs(query, service, time_range)
