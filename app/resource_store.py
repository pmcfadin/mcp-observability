from __future__ import annotations

"""In-memory store for MCP Resources with lazy loading from disk.

For this MVP we read a predefined set of files (README, Grafana dashboards)
into Resource models and allow simple list/read operations.
"""

from pathlib import Path
from threading import Lock
from typing import Dict, List

from mcp_observability.schemas import Resource, ResourceType

_BASE_DIR = Path(__file__).resolve().parent.parent

# Global cache protected by lock – this is not performance critical.
_resources_cache: List[Resource] | None = None
_lock = Lock()


def _load_resources() -> List[Resource]:
    readme_path = _BASE_DIR / "README.md"
    dashboard_path = _BASE_DIR / "grafana" / "dashboards" / "error_ops.json"

    resources: List[Resource] = []

    if readme_path.exists():
        resources.append(
            Resource(
                id="readme",
                type=ResourceType.text,
                name="Project README",
                description="Top-level project documentation",
                content=readme_path.read_text(encoding="utf-8"),
                metadata={"path": str(readme_path)},
            )
        )

    if dashboard_path.exists():
        resources.append(
            Resource(
                id="dashboard_error_ops",
                type=ResourceType.text,
                name="Grafana ErrorOps dashboard JSON",
                description="Pre-built dashboard visualising errors, latency, traces.",
                content=dashboard_path.read_text(encoding="utf-8"),
                metadata={"path": str(dashboard_path)},
            )
        )

    return resources


def list_resources() -> List[Resource]:
    global _resources_cache
    if _resources_cache is None:
        with _lock:
            if _resources_cache is None:
                _resources_cache = _load_resources()
    return _resources_cache


def get_resource(resource_id: str) -> Resource | None:
    for res in list_resources():
        if res.id == resource_id:
            return res
    return None 