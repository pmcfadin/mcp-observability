# Grafana Dashboards

This project bundles a set of pre-built dashboards that are automatically provisioned when you run the stack (Docker Compose or Helm).

| Screenshot | Title | Description | File |
|------------|-------|-------------|------|
| ![ErrorOps](images/error_ops.png) | **ErrorOps Overview** | Live view of recent errors (Loki), error rate, P95 latency (Prometheus) and correlated error traces (Tempo). | `grafana/dashboards/error_ops.json` |
| ![Node Exporter](images/16110.png) | **Node Exporter Full** (upstream id 16110) | System-level CPU, mem, disk, and network metrics. | `grafana/dashboards/16110.json` |
| ![Kubernetes Cluster](images/13175.png) | **Kubernetes Cluster Monitoring** (upstream id 13175) | Cluster health, workloads and resource utilisation. | `grafana/dashboards/13175.json` |

> Screenshots were captured locally from Grafana (`localhost:3000`) in dark mode at 1920×1080 and stored under `docs/images/`.

## Viewing dashboards locally

```bash
# Start the full stack
docker compose -f mcp-obs.yml up -d grafana

# Default credentials
open http://localhost:3000 (user: admin / admin)
```

Dashboards auto-load thanks to the provisioning config at `grafana/provisioning/dashboards.yaml`.

## Updating dashboards

* Upstream dashboards are refreshed by running:
  ```bash
  poetry run python scripts/fetch_dashboards.py
  ```
* Commit the resulting JSON changes so CI (dashboard-lint) can validate them. 