# Python Observability Guide – Sending Telemetry to MCP Observability

This document shows how to instrument a Python service with **OpenTelemetry** and forward traces, metrics, and logs to the local Docker Compose stack (`otel-collector`, `prometheus`, `loki`, `tempo`).

---

## 1 · Install dependencies

```bash
pip install opentelemetry-sdk opentelemetry-exporter-otlp opentelemetry-instrumentation
```

Optional log/metrics helpers:

```bash
pip install opentelemetry-instrumentation-logging opentelemetry-instrumentation-requests
```

---

## 2 · Configure environment variables

Assuming the stack is running on the same machine:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://localhost:4318"
export OTEL_SERVICE_NAME="my-python-app"
```

If `MCP_TOKEN` is required by `mcp-server` you still only need the collector URL; the collector forwards data internally.

## 2.1 · FastAPI specific setup

Install the FastAPI instrumentation shim:

```bash
pip install opentelemetry-instrumentation-fastapi
```

In your `main.py` (or wherever you create the ASGI app):

```python
from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.asgi import OpenTelemetryMiddleware

app = FastAPI()

# Attach instrumentation (captures requests, errors, latency)
FastAPIInstrumentor.instrument_app(app)
# optional: explicit middleware as alternative
# app.add_middleware(OpenTelemetryMiddleware)

@app.get("/hello")
async def hello():
    return {"msg": "hello"}
```

The instrumentation automatically creates spans for each request with attributes like `http.method`, `http.route`, `http.status_code`.

---

## 3 · Configure OTLP exporter towards mcp-observability

If you deployed **mcp-observability** via Docker Compose the default collector endpoint is `http://localhost:4318`.

For Kubernetes / remote clusters, point to the *otel-collector* `ClusterIP` service:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector.observability.svc:4318"
export OTEL_EXPORTER_OTLP_HEADERS="mcp-token=<YOUR_MCP_TOKEN>"
```

---

## 4 · Auto-instrumentation (recommended)

Use the OpenTelemetry launcher to patch popular libraries automatically:

```bash
opentelemetry-instrument \
  --traces_exporter otlp \
  --metrics_exporter otlp \
  --service_name my-python-app \
  python app.py
```

---

## 5 · View data in Grafana

1. Open <http://localhost:3000> (admin/admin by default).
2. Go to *Dashboards ▸ Browse ▸ Traces* to see spans, or *Browse ▸ Metrics* for latency graphs.
3. Use *Explore* to query logs:

   ```
   {service="my-python-app",level="error"}
   ```

---

## 6 · Troubleshooting

* **No spans appear** – confirm the `otel-collector` container is healthy and the endpoint URL/port are correct.
* **Connection refused** – ensure Docker Compose stack is running and port 4318 is not firewalled.
* **High cardinality warnings** – set `OTEL_ATTRIBUTE_COUNT_LIMIT`, `OTEL_SPAN_ATTRIBUTE_VALUE_LENGTH_LIMIT` as needed.

## 7 · AI Agent prompt (copy-paste)

> "You are an AI code assistant. Modify the existing FastAPI project to emit OpenTelemetry traces, metrics and logs to a remote OTLP endpoint. Requirements:\n\n* Use `opentelemetry-sdk>=1.25`, `opentelemetry-instrumentation-fastapi`, and `opentelemetry-exporter-otlp`.\n* Set exporter endpoint to `${OTEL_EXPORTER_OTLP_ENDPOINT}` and add `${MCP_TOKEN}` to `mcp-token` HTTP header.\n* Instrument FastAPI routes automatically and ensure startup/shutdown events are traced.\n* Capture HTTP client calls via `opentelemetry-instrumentation-requests`.\n* Output example `.env` file with OTEL variables."

Paste this into your preferred agent (e.g. Cursor, Claude) to auto-patch the service.

--- 