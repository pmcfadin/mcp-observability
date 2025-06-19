import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.security import verify_bearer_token

router = APIRouter(
    prefix="/traces",
    tags=["traces"],
    dependencies=[Depends(verify_bearer_token)],
)

LOKI_BASE_URL: str = os.getenv("LOKI_BASE_URL", "http://loki:3100")
TEMPO_BASE_URL: str = os.getenv("TEMPO_BASE_URL", "http://tempo:3200")


async def _fetch_trace_json(trace_id: str) -> Any:
    """Fetch raw trace JSON from Tempo/Jaeger HTTP API."""

    url = f"{TEMPO_BASE_URL.rstrip('/')}/api/traces/{trace_id}"

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to contact Tempo: {exc}",
            ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Tempo returned {response.status_code}",
        )

    return response.json()


async def _fetch_trace_logs(trace_id: str, limit: int) -> list[str]:
    """Fetch log lines from Loki associated with the given trace ID."""

    # Use Loki instant query filtering by trace_id label (common OTEL exporter label)
    url = f"{LOKI_BASE_URL.rstrip('/')}/loki/api/v1/query"
    params = {
        "query": f'{{trace_id="{trace_id}"}}',
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

    return lines[:limit]


@router.get(
    "/{trace_id}",
    status_code=status.HTTP_200_OK,
)
async def trace_json(trace_id: str) -> Any:
    """Return raw trace JSON for the given trace ID."""

    return await _fetch_trace_json(trace_id)


@router.get(
    "/{trace_id}/logs",
    status_code=status.HTTP_200_OK,
)
async def trace_logs(
    trace_id: str,
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, list[str]]:
    """Return log lines correlated with the specified trace."""

    logs = await _fetch_trace_logs(trace_id, limit)
    return {"logs": logs}
