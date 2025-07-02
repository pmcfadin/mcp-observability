# Developer Environment Setup

This guide walks you through getting the codebase **running, tested and linted** on your workstation.  It should take **≤ 10 minutes** on macOS, Linux or WSL.

> The project targets **Python 3.12**. Earlier versions are not supported.

---

## 1 · Required tooling

| Tool | Version | Purpose |
|------|---------|---------|
| **Python** | 3.12 (CPython) | Run the FastAPI server + tests |
| **Poetry** | ≥ 1.8 | Dependency & virtual-env manager |
| **Docker Desktop / Engine** | ≥ 20.10 | Boot the observability stack locally |
| **Docker Compose v2** | comes with Docker Desktop | Spins up the 7-container stack |
| **Git** | any | Source control |
| _(optional)_ **VS Code** + Python extension | latest | Recommended IDE |

Install examples (macOS/Homebrew):
```bash
brew install python@3.12
pipx install poetry  # pipx keeps Poetry isolated from site-packages
```

---

## 2 · Clone & install dependencies

```bash
git clone https://github.com/your-org/mcp-observability.git
cd mcp-observability

# Create the venv & install prod + dev deps
poetry install --with dev
```

Poetry will create `.venv/` inside the project. Activate it when running ad-hoc commands:
```bash
poetry shell  # optional; or prefix commands with `poetry run`
```

---

## 3 · Start the observability stack

The fastest way to run **all dependencies** (Prometheus, Loki, Tempo, etc.) is Docker Compose:
```bash
docker compose -f mcp-obs.yml up -d
```
Services will be reachable on the default ports – see the [Docker guide](../guides/docker.md) for full details.

---

## 4 · Running the API locally

With the stack up you can start the FastAPI server and have it hot-reload on code changes:
```bash
poetry run python -m app.main  # http://localhost:8000
```
Pass `--reload` env `ENV=dev` if you wire Uvicorn directly.

> **Tip:** you normally don't need to run the API manually when using Compose – the `mcp-server` container auto-reloads your code via bind-mount.

---

## 5 · Test & Lint

Run the unit test-suite:
```bash
poetry run pytest -q
```

Static checks:
```bash
poetry run black --check .
poetry run isort --check-only .
poetry run mypy app
```

Combine in one go:
```bash
./scripts/ci/check_drift.py   # example helper
```

> **pre-commit** – we don't use it yet; feel free to open a PR if you'd like automatic formatting.

---

## 6 · Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_TOKEN` | _none_ | Bearer token required for most endpoints. Set the **same value** inside Compose (`mcp-obs.yml`) and your curl/HTTP calls. |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://otel-collector:4318` | Where the API sends its own telemetry. |
| `GF_ADMIN_PASSWORD` | `admin` | Grafana admin password for local dashboards |

> You can export these in your terminal or create a `.env` file. Docker Compose picks them up automatically.

---

## 7 · Troubleshooting

| Symptom | Resolution |
|---------|-----------|
| `ImportError: cannot import name ...` | Make sure you're **inside** the Poetry venv (`poetry shell`). |
| `Address already in use :8000` | Another process is binding the port – change it in `app/main.py` or stop the other app. |
| Tests failing with TLS errors | Delete `certs/` and restart Compose to regenerate the self-signed CA. |

If you get stuck open an issue or ask in the project chat – we're happy to help!
