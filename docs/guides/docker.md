# Docker Getting Started – MCP Observability

This guide walks you through running **MCP Observability** locally via Docker Compose and exploring the bundled monitoring stack (Grafana, Prometheus, Loki, Tempo).

---

## 1 · Prerequisites

* Docker Desktop or Docker Engine 20.10+
* Docker Compose v2 (`docker compose` CLI) – installed automatically with Docker Desktop
* Optional: `curl` for quick API checks

---

## 2 · Clone the repo

```bash
git clone https://github.com/your-org/mcp-observability.git
cd mcp-observability
```

---

## 3 · Configure environment variables (optional)

| Variable | Purpose | Default |
|----------|---------|---------|
| `MCP_TOKEN` | Bearer-token required by the API and MCP tools | *none* (authentication disabled) |
| `GF_ADMIN_PASSWORD` | Grafana admin password | `admin` |

Example:

```bash
export MCP_TOKEN="s3cr3t"
export GF_ADMIN_PASSWORD="supersecret"
```

---

## 4 · Start the stack

```bash
docker compose -f mcp-obs.yml up -d
```

The command pulls pre-built images and starts the following containers:

| Service | Purpose | Host port |
|---------|---------|----------|
| `mcp-server` | FastAPI application (TLS, requires `MCP_TOKEN`) | 8000 (HTTPS) |
| `grafana` | Dashboards UI | 3000 |
| `prometheus` | Metrics store | 9090 |
| `loki` | Logs store | 3100 |
| `tempo` | Traces backend | 3200 |
| `otel-collector` | OpenTelemetry gateway | 4317 (gRPC), 4318 (HTTP) |

> NOTE – the default Compose file uses **ephemeral named volumes**. Data disappears when you run `docker compose down -v`.

---

## 5 · Verify the stack

1. **Grafana** – open <http://localhost:3000> and log in with the admin credentials.
   * Dashboards live in the *General* folder (Latency, Error Rate, Traces…).
2. **API health** – if `MCP_TOKEN` is set:

   ```bash
   curl -k -H "Authorization: Bearer $MCP_TOKEN" https://localhost:8000/health
   # → {"status":"ok"}
   ```
3. **Prometheus** – <http://localhost:9090>
4. **Loki** – query UI at <http://localhost:3100>
5. **Tempo** – Jaeger UI at <http://localhost:3200>

---

## 6 · Stopping & cleaning up

```bash
docker compose -f mcp-obs.yml down             # stop containers (volumes persist)
docker compose -f mcp-obs.yml down -v          # stop & delete volumes (data loss)
```

---

## 7 · Troubleshooting

* **Ports already in use** – adjust the ports in `mcp-obs.yml` or stop the conflicting services.
* **Certificate warnings** – the stack uses self-signed TLS certificates; pass `-k` to `curl` or import `certs/ca.crt` into your browser.
* **No dashboards** – ensure `./grafana/provisioning` and `./grafana/dashboards` are mounted (default). 

## Local Development Workflow

This guide walks you through spinning up the **full observability stack** on your laptop with Docker Compose, sending some demo telemetry, and interacting with the MCP API.

> **TL;DR**
> ```bash
> # clone repo & cd inside
> export MCP_TOKEN=changeme
> docker compose -f mcp-obs.yml up -d
> open http://localhost:3000           # Grafana UI
> curl -k -H "Authorization: Bearer $MCP_TOKEN" https://localhost:8000/health
> ```

---

## 1 · Prerequisites

* Docker Desktop ≥ 24 or Podman ≥ 4.0
* `git` (to clone the repo)
* (Optional) `curl`, `grpcurl`, or the **MCP CLI** for testing the API

> ⚠️ **Ports in use**
> | Service | Port |
> | ------- | ---- |
> | MCP Server | `8000` (HTTPS) |
> | Grafana | `3000` (HTTP) |
> | Prometheus | `9090` |
> | Alertmanager | `9093` |
> | Loki | `3100` |
> | Tempo/Jaeger | `3200` |
>
> Adjust the published ports in `mcp-obs.yml` if they clash with local services.

---

## 2 · Boot the stack

```bash
# 1) clone & enter repo
 git clone https://github.com/your-org/mcp-observability.git
 cd mcp-observability

# 2) choose an auth token
 export MCP_TOKEN=changeme

# 3) spin it up
 docker compose -f mcp-obs.yml up -d
```

Compose starts **nine** containers:

* `otep-collector`, `prometheus`, `loki`, `tempo`, `grafana`
* `mcp-server` – the API we care about
* `mcp-certgen` – generates a CA plus server/client certs for mTLS in `/certs`

Check status:

```bash
docker compose ps
```

---

## 3 · First requests

### 3.1 Health probe

```bash
curl -k -H "Authorization: Bearer $MCP_TOKEN" \
     https://localhost:8000/health
# → {"status":"ok"}
```

> `-k` skips certificate verification because the stack uses a **self-signed** CA.
> If you want proper verification, trust the CA instead:
>
> ```bash
> sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain certs/ca.crt  # macOS
> ```

### 3.2 Query recent error logs

```bash
curl -k -H "Authorization: Bearer $MCP_TOKEN" \
     "https://localhost:8000/logs/errors?limit=5&range=1h"
```

### 3.3 Tempo trace drill-down

1. Open Grafana → Tempo → find a recent trace ID.
2. Fetch via MCP:

```bash
curl -k -H "Authorization: Bearer $MCP_TOKEN" \
     https://localhost:8000/traces/<trace_id>
```

---

## 4 · Developing against the stack

| Task | How-to |
| ---- | ------- |
| **Add new API endpoint** | Edit `app/*.py`, write a test in `tests/`, run `pytest`. |
| **View live spans**      | Tempo UI (`Explore → Tempo`) or `docker logs mcp-server` to see exporter debug. |
| **Inject sample data**   | Use `otelcol --config <file>` to tail container logs, or run the [OpenTelemetry demo app](https://github.com/open-telemetry/opentelemetry-demo). |

---

## 5 · Common Scenarios

### Scenario A – Debugging a failing micro-service test locally

1. Run the application under test with `OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318` so traces are shipped into the collector.
2. Re-run your failing integration test.
3. Ask MCP for the last 20 error logs:
   ```bash
   curl -k -H "Authorization: Bearer $MCP_TOKEN" \
        "https://localhost:8000/logs/errors?service=my-svc&limit=20&range=15m"
   ```
4. Grab a trace ID from the log line and fetch the full trace JSON via MCP.
5. Inspect spans / SQL durations in the Tempo UI.

### Scenario B – Performance regression hunt

```bash
# Compare p95 latency over the last 30 min vs same yesterday
curl -k -H "Authorization: Bearer $MCP_TOKEN" \
     "https://localhost:8000/metrics/latency?window=30m&percentile=0.95&service=api-gateway"
```

If the value exceeds your SLA, your script/bot can call `/alerts` or post to Slack.

---

## 6 · Shutting down & cleanup

```bash
docker compose -f mcp-obs.yml down -v   # removes containers & named volumes
```

⚠️ `-v` deletes Prometheus / Loki data stored in named volumes. Omit if you want to keep test data. 