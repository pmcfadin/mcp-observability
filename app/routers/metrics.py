import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel as _PydanticBaseModel

from app.security import verify_bearer_token

router = APIRouter(
    prefix="/metrics",
    tags=["metrics"],
    dependencies=[Depends(verify_bearer_token)],
)

PROMETHEUS_BASE_URL: str = os.getenv("PROMETHEUS_BASE_URL", "http://prometheus:9090")


async def _fetch_latency_percentile(
    percentile: float, window: str, service: str | None = None
) -> float:
    """Query Prometheus for latency percentile over the given window.

    Uses the `histogram_quantile` function on the `http_server_request_duration_seconds_bucket` metric.
    Returns the latency in seconds as a float.
    """

    # Build PromQL, optionally scoping to service label
    metric = "http_server_request_duration_seconds_bucket"
    if service:
        metric = f'{metric}{{service="{service}"}}'

    promql = (
        f"histogram_quantile({percentile}, " f"sum(rate({metric}[{window}])) by (le))"
    )

    url = f"{PROMETHEUS_BASE_URL.rstrip('/')}/api/v1/query"
    params = {"query": promql}

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url, params=params)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to contact Prometheus: {exc}",
            ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Prometheus returned {response.status_code}",
        )

    data: Any = response.json()
    try:
        result = data["data"]["result"][0]["value"][1]
    except (KeyError, IndexError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected Prometheus response format",
        ) from exc

    try:
        return float(result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Prometheus returned non-numeric value",
        ) from exc


@router.get(
    "/latency",
    status_code=status.HTTP_200_OK,
)
async def metrics_latency(
    percentile: float = Query(0.95, gt=0.0, lt=1.0),
    window: str = Query("5m", pattern=r"^\d+[smhd]$"),
    service: str | None = Query(None, pattern=r"^[a-zA-Z0-9_-]+$"),
) -> dict[str, float | str]:
    """Return latency percentile over window from Prometheus.

    Example: `/metrics/latency?percentile=0.99&window=1m`
    """

    latency = await _fetch_latency_percentile(percentile, window, service)
    return {
        "percentile": percentile,
        "window": window,
        "latency_seconds": latency,
        **({"service": service} if service else {}),
    }


class PrometheusQueryRequest(_PydanticBaseModel):
    query: str


async def _execute_promql(promql: str) -> Any:
    """Execute an arbitrary PromQL query against Prometheus instant query API.

    Returns the raw `data.result` portion of the response JSON (list).
    """

    url = f"{PROMETHEUS_BASE_URL.rstrip('/')}/api/v1/query"
    params = {"query": promql}

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url, params=params)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to contact Prometheus: {exc}",
            ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Prometheus returned {response.status_code}",
        )

    data: Any = response.json()
    try:
        return data["data"]["result"]
    except (KeyError, TypeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected Prometheus response format",
        ) from exc


@router.post(
    "/query",
    status_code=status.HTTP_200_OK,
)
async def metrics_query(request: PrometheusQueryRequest) -> dict[str, Any]:
    """Execute an arbitrary PromQL instant query and return the raw result list."""

    result = await _execute_promql(request.query)
    return {"result": result}
