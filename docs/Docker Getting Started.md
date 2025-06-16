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

The command builds / pulls images and starts the following containers:

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