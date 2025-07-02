# Observability & Telemetry

The MCP service is fully instrumented with OpenTelemetry.  Spans for every
HTTP request as well as outgoing HTTPX calls are exported to the endpoint
specified by the `OTEL_EXPORTER_OTLP_ENDPOINT` environment variable (defaults
to `http://otel-collector:4318`).

## 1. Local stack

`docker compose -f mcp-obs.yml up` starts an OpenTelemetry Collector plus the
Grafana/Tempo/Loki/Prometheus stack.  Open the **Grafana** UI at
<http://localhost:3000> and explore:

* **Tempo** tab → Traces for `service.name = mcp-observability`
* **Prometheus** tab → Metric `http_server_request_duration_seconds_bucket`
* **Loki** tab → Log streams with trace correlation (`trace_id` label)

## 2. Custom collector

Deploy your own collector and point the service at it:

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=https://otel.mycorp.net:4318
```

## 3. Metrics endpoint

In addition to OTLP, the service exposes Prometheus metrics (via the
OpenTelemetry Prometheus exporter) at `/metrics` on the same port.

## 4. Dashboards

Under `grafana/dashboards/` JSON dashboard definitions are provisioned
automatically when running the stack.  Copy them to your central Grafana for a
quick start.
