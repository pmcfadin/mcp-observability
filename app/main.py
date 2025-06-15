from fastapi import Depends, FastAPI, status, Query, HTTPException

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


def run() -> None:  # pragma: no cover
    """Run the application using uvicorn when executed as a module."""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":  # pragma: no cover
    run() 