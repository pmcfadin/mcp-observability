from fastapi import Depends, FastAPI, status

from app.routers import alerts, logs, metrics, traces
from app.security import verify_bearer_token

app = FastAPI(title="MCP Observability API")

from app.initialize import router as initialize_router  # noqa: E402
from app.manifest import router as manifest_router  # noqa: E402
from app.prompts import router as prompts_router  # noqa: E402

# Include MCP feature routers (Resources, Prompts, Sampling, ...)
from app.resources import (  # noqa: E402  (circular import tolerated at runtime)
    router as resources_router,
)
from app.sampling import router as sampling_router  # noqa: E402

app.include_router(resources_router)
app.include_router(prompts_router)
app.include_router(sampling_router)
app.include_router(initialize_router)
app.include_router(manifest_router)
app.include_router(alerts.router)
app.include_router(logs.router)
app.include_router(metrics.router)
app.include_router(traces.router)

# ---------------------------------------------------------------------
# Observability – tracing & metrics via OpenTelemetry
# ---------------------------------------------------------------------
from app.otel_setup import configure_opentelemetry  # noqa: E402

configure_opentelemetry(app)


@app.get(
    "/health",
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(verify_bearer_token)],
)
async def health() -> dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}


def run() -> None:  # pragma: no cover
    """Run the application using uvicorn when executed as a module."""
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":  # pragma: no cover
    run()
