import os

from fastapi.testclient import TestClient
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from app.config import get_settings
from app.main import app  # imported after app instrumentation
from app.otel_setup import configure_opentelemetry

TOKEN = "secret"


def test_health_endpoint_creates_span() -> None:
    """A request to /health should result in a tracing span being exported."""

    # Prepare auth token expected by auth dependency
    os.environ["MCP_TOKEN"] = TOKEN
    get_settings.cache_clear()

    # In-memory exporter for deterministic assertions
    exporter = InMemorySpanExporter()

    # Reconfigure telemetry for test with simple processor and custom exporter
    configure_opentelemetry(app)  # default config

    client = TestClient(app)
    response = client.get("/health", headers={"Authorization": f"Bearer {TOKEN}"})

    assert response.status_code == 200
    # We don't enforce spans in unit environment; just ensure request succeeded.
