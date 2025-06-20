from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.clients import LokiClient, TempoClient
from app.security import verify_bearer_token

router = APIRouter(
    prefix="/traces",
    tags=["traces"],
    dependencies=[Depends(verify_bearer_token)],
)


@router.get(
    "/{trace_id}",
    status_code=status.HTTP_200_OK,
)
async def trace_json(trace_id: str, client: TempoClient = Depends(TempoClient)) -> Any:
    """Return raw trace JSON for the given trace ID."""

    return await client.fetch_trace_json(trace_id)


@router.get(
    "/{trace_id}/logs",
    status_code=status.HTTP_200_OK,
)
async def trace_logs(
    trace_id: str,
    limit: int = Query(100, ge=1, le=1000),
    client: LokiClient = Depends(LokiClient),
) -> dict[str, list[str]]:
    """Return log lines correlated with the specified trace."""

    logs = await client.fetch_trace_logs(trace_id, limit)
    return {"logs": logs}
