from typing import Any, List

from mcp.server.fastmcp import FastMCP

from app.main import (_fetch_error_logs, _fetch_latency_percentile,
                      _fetch_trace_json, _fetch_trace_logs, _search_logs)

mcp = FastMCP("mcp-observability-server")


@mcp.tool(description="Return simple health status")
async def health() -> str:  # type: ignore[override]
    """Health check tool (returns \"ok\")."""

    return "ok"


@mcp.tool(description="Fetch last N error log lines from Loki")
async def error_logs(limit: int = 100) -> List[str]:  # type: ignore[override]
    """Return the last *limit* error log lines from Loki.

    Args:
        limit: Number of lines to return (1-1000).
    """

    # Clamp limit to allowed bounds in helper
    return await _fetch_error_logs(limit)


@mcp.tool(description="Query Prometheus latency percentile over window")
async def latency_percentile(
    percentile: float = 0.95,
    window: str = "5m",
) -> float:  # type: ignore[override]
    """Return latency percentile from Prometheus.

    Args:
        percentile: Target percentile (0<percentile<1).
        window: Prometheus range vector duration (e.g. 1m, 5m, 1h).
    """

    return await _fetch_latency_percentile(percentile, window)


@mcp.tool(description="Return raw trace JSON for given trace_id")
async def trace_json_tool(trace_id: str) -> Any:  # type: ignore[override]
    return await _fetch_trace_json(trace_id)


@mcp.tool(description="Return log lines correlated with trace_id")
async def trace_logs_tool(trace_id: str, limit: int = 100) -> list[str]:  # type: ignore[override]
    return await _fetch_trace_logs(trace_id, limit)


# Log search tool -----------------------------------------------------------


@mcp.tool(description="Search logs by query and optional service")
async def logs_search_tool(query: str, service: str | None = None, range: str | None = "1h") -> list[str]:  # type: ignore[override]
    return await _search_logs(query, service, range)


# Metrics query tool --------------------------------------------------------


@mcp.tool(description="Execute PromQL query and return raw result list")
async def metrics_query(query: str) -> Any:  # type: ignore[override]
    from app.main import _execute_promql

    return await _execute_promql(query)


# Alerts tool --------------------------------------------------------------


@mcp.tool(description="Return active alerts from Alertmanager filtered by severity/service")
async def alerts_tool(severity: str | None = None, service: str | None = None) -> list[dict[str, Any]]:  # type: ignore[override]
    from app.main import _fetch_active_alerts

    return await _fetch_active_alerts(severity, service)


if __name__ == "__main__":  # pragma: no cover
    mcp.run()
