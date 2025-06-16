from fastapi import Depends, FastAPI, HTTPException, Query, status

from app.security import verify_bearer_token

app = FastAPI(title="MCP Observability API")


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_bearer_token)],
)
async def health() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


# --- Logs ------------------------------------------------------------------

import os
from typing import Any, List

import httpx

LOKI_BASE_URL: str = os.getenv("LOKI_BASE_URL", "http://loki:3100")


async def _fetch_error_logs(limit: int) -> List[str]:
    """Fetch the last *limit* error log lines from Loki.

    The function performs a GET request to Loki's *instant* query API using a
    label matcher that filters for logs with level="error". Only the log line
    strings are returned, newest first.
    """

    # Loki instant query endpoint; we rely on the default tenant and time=now.
    url = f"{LOKI_BASE_URL.rstrip('/')}/loki/api/v1/query"
    params = {
        "query": '{level="error"}',  # simple filter; adjust if needed
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


@app.get(
    "/logs/errors",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_bearer_token)],
)
async def logs_errors(limit: int = Query(100, ge=1, le=1000)) -> dict[str, list[str]]:
    """Return the last *limit* error log lines from Loki.

    The endpoint proxies a query to the Loki HTTP API, returning only the raw
    log lines so that API consumers do not need to know Loki's schema.
    """

    logs = await _fetch_error_logs(limit)
    return {"logs": logs}


# --- Log Search ------------------------------------------------------------


from pydantic import BaseModel


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


@app.post(
    "/logs/search",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_bearer_token)],
)
async def logs_search(request: LogSearchRequest) -> dict[str, list[str]]:
    """Return log lines matching query (and optional service) from Loki."""

    logs = await _search_logs(request.query, request.service, request.range)
    return {"logs": logs}


# --- Metrics ---------------------------------------------------------------

PROMETHEUS_BASE_URL: str = os.getenv("PROMETHEUS_BASE_URL", "http://prometheus:9090")


async def _fetch_latency_percentile(percentile: float, window: str) -> float:
    """Query Prometheus for latency percentile over the given window.

    Uses the `histogram_quantile` function on the `http_server_request_duration_seconds_bucket` metric.
    Returns the latency in seconds as a float.
    """

    promql = (
        f"histogram_quantile({percentile}, "
        f"sum(rate(http_server_request_duration_seconds_bucket[{window}])) by (le))"
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


@app.get(
    "/metrics/latency",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_bearer_token)],
)
async def metrics_latency(
    percentile: float = Query(0.95, gt=0.0, lt=1.0),
    window: str = Query("5m", pattern=r"^\d+[smhd]$"),
) -> dict[str, float | str]:
    """Return latency percentile over window from Prometheus.

    Example: `/metrics/latency?percentile=0.99&window=1m`
    """

    latency = await _fetch_latency_percentile(percentile, window)
    return {
        "percentile": percentile,
        "window": window,
        "latency_seconds": latency,
    }


# --- Traces ----------------------------------------------------------------

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


@app.get(
    "/traces/{trace_id}",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_bearer_token)],
)
async def trace_json(trace_id: str) -> Any:
    """Return raw trace JSON for the given trace ID."""

    return await _fetch_trace_json(trace_id)


@app.get(
    "/traces/{trace_id}/logs",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_bearer_token)],
)
async def trace_logs(
    trace_id: str,
    limit: int = Query(100, ge=1, le=1000),
) -> dict[str, list[str]]:
    """Return log lines correlated with the specified trace."""

    logs = await _fetch_trace_logs(trace_id, limit)
    return {"logs": logs}


# --- Metrics Query ---------------------------------------------------------

from pydantic import BaseModel as _PydanticBaseModel


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


@app.post(
    "/metrics/query",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_bearer_token)],
)
async def metrics_query(request: PrometheusQueryRequest) -> dict[str, Any]:
    """Execute an arbitrary PromQL instant query and return the raw result list."""

    result = await _execute_promql(request.query)
    return {"result": result}


# --- Alerts ----------------------------------------------------------------

ALERTMANAGER_BASE_URL: str = os.getenv("ALERTMANAGER_BASE_URL", "http://alertmanager:9093")


async def _fetch_active_alerts(severity: str | None = None, service: str | None = None) -> list[dict[str, Any]]:
    """Fetch active alerts from Alertmanager and filter by severity/service if given."""

    url = f"{ALERTMANAGER_BASE_URL.rstrip('/')}/api/v2/alerts"

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to contact Alertmanager: {exc}",
            ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Alertmanager returned {response.status_code}",
        )

    alerts: Any = response.json()
    if not isinstance(alerts, list):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unexpected Alertmanager response format")

    def _matches(alert: dict[str, Any]) -> bool:
        labels = alert.get("labels", {})
        if severity and labels.get("severity") != severity:
            return False
        if service and labels.get("service") != service:
            return False
        return True

    return [a for a in alerts if _matches(a)]


@app.get(
    "/alerts",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_bearer_token)],
)
async def alerts(
    severity: str | None = Query(None, pattern=r"^[a-zA-Z0-9_-]+$"),
    service: str | None = Query(None, pattern=r"^[a-zA-Z0-9_-]+$"),
) -> dict[str, list[dict[str, Any]]]:
    """Return active alerts filtered by optional severity and service labels."""

    active_alerts = await _fetch_active_alerts(severity, service)
    return {"alerts": active_alerts}


def run() -> None:  # pragma: no cover
    """Run the application using uvicorn when executed as a module."""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":  # pragma: no cover
    run()
