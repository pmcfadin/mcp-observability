from typing import Any

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel as _PydanticBaseModel

from app.clients import PrometheusClient
from app.security import verify_bearer_token

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    dependencies=[Depends(verify_bearer_token)],
)


@router.get(
    "/latency",
    status_code=status.HTTP_200_OK,
)
async def metrics_latency(
    percentile: float = Query(0.95, gt=0.0, lt=1.0),
    window: str = Query("5m", pattern=r"^\d+[smhd]$"),
    service: str | None = Query(None, pattern=r"^[a-zA-Z0-9_-]+$"),
    client: PrometheusClient = Depends(PrometheusClient),
) -> dict[str, float | str]:
    """Return latency percentile over window from Prometheus.

    Example: `/metrics/latency?percentile=0.99&window=1m`
    """

    latency = await client.fetch_latency_percentile(percentile, window, service)
    return {
        "percentile": percentile,
        "window": window,
        "latency_seconds": latency,
        **({"service": service} if service else {}),
    }


class PrometheusQueryRequest(_PydanticBaseModel):
    query: str


@router.post(
    "/query",
    status_code=status.HTTP_200_OK,
)
async def metrics_query(
    request: PrometheusQueryRequest,
    client: PrometheusClient = Depends(PrometheusClient),
) -> dict[str, Any]:
    """Execute an arbitrary PromQL instant query and return the raw result list."""

    result = await client.execute_promql(request.query)
    return {"result": result}
