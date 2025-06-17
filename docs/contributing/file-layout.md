# Source File Layout

This page drills down into the **directory structure** of the repository and highlights key files you are likely to touch when contributing.

```
.
├── app/                    # FastAPI application + domain modules
│   ├── main.py             # FastAPI entrypoint (uvicorn)
│   ├── grpc_server.py      # gRPC (MCP) entrypoint
│   ├── resources.py        # Resource endpoint implementation
│   └── ...                 # Other helpers & submodules
├── mcp_observability/      # Shared protobuf + Pydantic schemas
│   └── proto/              # observability.proto (gRPC)
├── charts/mcp-obs/         # Helm chart (values.yaml, templates/)
├── mcp-obs.yml             # Docker Compose manifest for local dev
├── grafana/                # Provisioned dashboards & datasources
├── docs/                   # Project & user documentation
│   ├── guides/             # User how-to guides (Docker, K8s…)
│   ├── observability/      # Language-specific instrumentation guides
│   └── contributing/       # You are here
├── scripts/                # Utility scripts (CI, certgen, docs…)
│   └── ci/                 # Release automation, drift checks, etc.
├── tests/                  # Pytest suite
├── pyproject.toml          # Poetry project metadata & deps
└── README.md               # Entry-point for users & contributors
```

## Key development hotspots

| Path | Why you might edit it |
|------|----------------------|
| `app/` | Add/modify API endpoints, business logic, auth rules. |
| `tests/` | Write tests for your new functionality. |
| `charts/mcp-obs/` | Extend Helm deployment options. |
| `mcp-obs.yml` | Keep in sync with Helm chart for local parity. |
| `grafana/dashboards/` | Update or add Grafana dashboards JSON. |
| `scripts/` | Add helper scripts for CI, docs or maintenance tasks. |

## How the pieces fit together

1. **Develop/Run locally** – `docker compose -f mcp-obs.yml up -d` boots the stack and mounts your live code into the `mcp-server` container for hot-reload.
2. **Unit tests** – run `poetry run pytest -q` to verify endpoints and helpers.
3. **CI** – GitHub Actions lint & test on every push; drift check ensures Compose ≙ Helm.
4. **Deploy** – `helm install` or update Compose file → same container images run anywhere.

For a full architectural overview see `architecture-overview.md`. 