# Partial Component Deployment Guide – MCP Observability

> Deploy **only the parts you need** – save resources while still integrating with your existing logging, metrics or tracing backend.

---

## 1 · Why partial deployments?

Many organisations already run Prometheus, Grafana or an APM solution. MCP-Observability is modular: you can install only the `mcp-server` (API) and whichever collectors / UIs you are missing.

Typical scenarios:

| Use-case | Required components |
|----------|--------------------|
| **Metrics-only** | mcp-server + Prometheus + Grafana |
| **Logs-only** | mcp-server + Loki + Grafana |
| **Traces-only** | mcp-server + Tempo + Grafana |
| **API gateway** | mcp-server only (integrate with external data stores) |

---

## 2 · Docker Compose overrides

The default `docker-compose.yml` starts *all* services. Create an override file that disables what you don't want:

```yaml
# compose.metrics.yml – metrics-only
services:
  loki:
    deploy:
      replicas: 0
  tempo:
    deploy:
      replicas: 0
```

Run with:

```bash
docker compose -f docker-compose.yml -f compose.metrics.yml up -d
```

Guides for other modes:

* `compose.logs.yml` – disable Prometheus + Tempo
* `compose.traces.yml` – disable Prometheus + Loki
* `compose.api.yml` – disable all except `mcp-server`

---

## 3 · Helm values overrides

Every chart sub-component has an `enabled` flag. Example *logs-only* install (Grafana + Loki):

```bash
helm install mcp charts/mcp-obs \
  --set prometheus.enabled=false \
  --set tempo.enabled=false \
  --set otelCollector.enabled=false
```

For a pure API deployment:

```bash
helm install mcp charts/mcp-obs --set grafana.enabled=false,loki.enabled=false,prometheus.enabled=false,tempo.enabled=false,otelCollector.enabled=false
```

---

## 4 · Resource sizing

Component | CPU (req/lim) | Memory (req/lim)
---|---|---
`mcp-server` | 100m / 500m | 128Mi / 512Mi
Grafana | 50m / 300m | 128Mi / 256Mi
Prometheus | 200m / 1 | 256Mi / 2Gi
Loki | 100m / 500m | 128Mi / 512Mi
Tempo | 100m / 500m | 128Mi / 512Mi

Adjust based on ingest volume & retention.

---

## 5 · Troubleshooting

| Symptom | Likely cause | Fix |
|----------|-------------|-----|
| API returns 5xx on metrics endpoint | Prometheus disabled but `metrics.enabled=true` on client | Disable metrics exporter in client or deploy Prometheus |
| Grafana dashboards show "No data" | Component disabled/not scraping | Verify service endpoints & datasource list |
| `otel-collector` crashes | Collector disabled but forwarding configured | Remove collector exporter from client config or enable component |

---

Need more help? Open an issue referencing this guide with logs & configuration for quicker assistance. 