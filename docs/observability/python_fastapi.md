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

---

## 3 · Manual instrumentation example

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# 1. Configure tracer provider
resource = Resource.create({"service.name": "my-python-app"})
provider = TracerProvider(resource=resource)
trace.set_tracer_provider(provider)

# 2. Add OTLP HTTP exporter (collector)
exporter = OTLPSpanExporter(endpoint="http://localhost:4318/v1/traces")
provider.add_span_processor(BatchSpanProcessor(exporter))

tracer = trace.get_tracer(__name__)

# 3. Create spans in your code
with tracer.start_as_current_span("demo-operation"):
    print("Doing work…")
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