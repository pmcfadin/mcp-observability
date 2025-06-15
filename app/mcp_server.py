from typing import List

from mcp.server.fastmcp import FastMCP

from app.main import _fetch_error_logs, _fetch_latency_percentile

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


if __name__ == "__main__":  # pragma: no cover
    mcp.run() 