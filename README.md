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