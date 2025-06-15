# MCP Observability FastAPI Service

This service exposes health, log, and metric endpoints that will be consumed by the MCP Observability platform.

## Quick start (development)

```bash
# Install Poetry if you don't have it
pipx install poetry

# Install dependencies (Python 3.12)
poetry install --with dev

# Run the application with hot-reload
poetry run python -m app.main
```

Then visit `http://localhost:8000/health` to verify the service is running.

## Tests

```bash
poetry run pytest -q
```

## Linting / Type-checking

```bash
poetry run black --check .
poetry run isort --check-only .
poetry run mypy app
```

## Deployment

### Local (Docker Compose)

```bash
# Start all components (fast, ephemeral storage)
docker compose -f mcp-obs.yml up -d

# Tear down
# docker compose -f mcp-obs.yml down -v
```

Services started:
* `mcp-server` – FastAPI application (port 8000)
* `grafana` – Dashboards UI (port 3000, default admin \`admin/admin\`)
* `prometheus` – Metrics (port 9090)
* `loki` – Logs (port 3100)
* `tempo` – Traces (port 3200)
* `otel-collector` – OpenTelemetry entry point (ports 4317/4318)

The default Compose file uses **ephemeral named volumes**. Data vanishes on `down -v`. If you need persistence, map the volumes to host paths or use the Helm chart below.

### Kubernetes (Helm)

Prerequisites: Helm v3.12+ and access to a cluster.

```bash
# Update chart dependencies
ahelm dependency update charts/mcp-obs

# Install into namespace "observability"
helm install mcp charts/mcp-obs \
  --namespace observability --create-namespace \
  --set grafana.persistence.enabled=true \
  --set loki.persistence.enabled=true \
  --set prometheus.server.persistentVolume.enabled=true \
  --set tempo.persistence.enabled=true
```

Alternatively provide a `my-values.yaml`:

```yaml
persistence:
  enabled: true  # convenience flag (does **not** auto-propagate)

loki:
  persistence:
    enabled: true
    size: 10Gi
# ... other component overrides ...
```

```bash
helm install mcp charts/mcp-obs -f my-values.yaml --namespace observability --create-namespace
```

### Drift detection in CI
A GitHub Actions workflow (`.github/workflows/drift-check.yml`) automatically compares the services defined in `mcp-obs.yml` with the Helm chart dependencies. Pull requests touching either manifest will fail if they diverge. 