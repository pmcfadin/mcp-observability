import os
from typing import Any, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.security import verify_bearer_token

router = APIRouter(
    prefix="/logs",
    tags=["logs"],
    dependencies=[Depends(verify_bearer_token)],
)

LOKI_BASE_URL: str = os.getenv("LOKI_BASE_URL", "http://loki:3100")


async def _fetch_error_logs(
    limit: int, service: str | None = None, time_range: str | None = None
) -> List[str]:
    """Fetch recent error log lines from Loki.

    Args:
        limit: Maximum number of lines to return.
        service: Optional service label to filter on.
        time_range: Optional LogQL range selector (e.g., 1h, 24h). When
            provided, the query restricts the time window using a range
            vector. Loki instant queries support the syntax
            `{selector}[range]`.
    """

    selector = '{level="error"}'
    if service:
        selector = f'{{level="error",service="{service}"}}'

    query_str = selector
    if time_range:
        query_str = f"{selector}[{time_range}]"

    url = f"{LOKI_BASE_URL.rstrip('/')}/loki/api/v1/query"
    params = {
        "query": query_str,
        "limit": str(limit),
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url, params=params)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to contact Loki: {exc}",
            ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Loki returned {response.status_code}",
        )

    data: Any = response.json()
    # Expected structure: {"data": {"result": [ {"values": [[ts, line], ...]} ] } }
    try:
        results = data["data"]["result"]
    except (KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected Loki response format",
        ) from exc

    lines: List[str] = []
    for stream in results:
        for _ts, line in stream.get("values", []):
            lines.append(line)

    # Loki returns newest first within each stream; we preserve order as‐is.
    return lines[:limit]


@router.get(
    "/errors",
    status_code=status.HTTP_200_OK,
)
async def logs_errors(
    limit: int = Query(100, ge=1, le=1000),
    service: str | None = Query(None, pattern=r"^[a-zA-Z0-9_-]+$"),
    range: str | None = Query(None, pattern=r"^\d+[smhd]$"),
) -> dict[str, list[str]]:
    """Return the last *limit* error log lines from Loki.

    The endpoint proxies a query to the Loki HTTP API, returning only the raw
    log lines so that API consumers do not need to know Loki's schema.
    """

    logs = await _fetch_error_logs(limit, service, range)
    return {"logs": logs}


class LogSearchRequest(BaseModel):
    query: str
    service: str | None = None
    range: str | None = "1h"


async def _search_logs(
    query: str, service: str | None, time_range: str | None
) -> list[str]:
    """Search Loki logs for query within optional service and time range."""

    selector = "{}"
    if service:
        selector = f'{{service="{service}"}}'

    # Use simple LogQL contains match; callers can pass regex if needed
    logql = f'{selector} |= "{query}"'

    url = f"{LOKI_BASE_URL.rstrip('/')}/loki/api/v1/query"
    params = {"query": logql, "limit": "1000"}

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url, params=params)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to contact Loki: {exc}",
            ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Loki returned {response.status_code}",
        )

    data: Any = response.json()
    try:
        results = data["data"]["result"]
    except (KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected Loki response format",
        ) from exc

    lines: list[str] = []
    for stream in results:
        for _ts, line in stream.get("values", []):
            lines.append(line)

    return lines


@router.post(
    "/search",
    status_code=status.HTTP_200_OK,
)
async def logs_search(request: LogSearchRequest) -> dict[str, list[str]]:
    """Return log lines matching query (and optional service) from Loki."""

    logs = await _search_logs(request.query, request.service, request.range)
    return {"logs": logs}
