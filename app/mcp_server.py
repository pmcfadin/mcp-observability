from typing import List, Any

from mcp.server.fastmcp import FastMCP

from app.main import _fetch_error_logs, _fetch_latency_percentile, _fetch_trace_json, _fetch_trace_logs

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


if __name__ == "__main__":  # pragma: no cover
    mcp.run() 