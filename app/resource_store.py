from __future__ import annotations

"""In-memory store for MCP Resources with lazy loading from disk.

For this MVP we read a predefined set of files (README, Grafana dashboards)
into Resource models and allow simple list/read operations.
"""

from pathlib import Path
from threading import Lock
from typing import Dict, List

from mcp_observability.schemas import Resource, ResourceTemplate, ResourceType

_BASE_DIR = Path(__file__).resolve().parent.parent

# Global cache protected by lock – this is not performance critical.
_resources_cache: List[Resource] | None = None
_lock = Lock()

# ---------------------------------------------------------------------------
# Resource templates (dynamic) ------------------------------------------------
# ---------------------------------------------------------------------------

_resource_templates: List[ResourceTemplate] | None = None


def list_templates() -> List[ResourceTemplate]:
    """Return dynamic resource URI templates.

    1. Loki queries – expr parameter: `loki://query{?expr}`
    2. Runbook markdown in docs/runbooks/<slug>.md: `runbook://{slug}`
    """

    global _resource_templates
    if _resource_templates is not None:
        return _resource_templates

    templates: List[ResourceTemplate] = [
        ResourceTemplate(
            uri_template="loki://query{?expr}",
            name="Loki query expression",
            description="Execute a Loki log query using the provided expr parameter.",
            mimeType="application/json",
        ),
        ResourceTemplate(
            uri_template="runbook://{slug}",
            name="Operational runbook markdown",
            description="Markdown runbook located under docs/runbooks/.",
            mimeType="text/markdown",
        ),
    ]

    _resource_templates = templates
    return templates


def _load_resources() -> List[Resource]:
    resources: List[Resource] = []

    # 1. Top-level README ----------------------------------------------------------------
    readme_path = _BASE_DIR / "README.md"
    if readme_path.exists():
        resources.append(
            Resource(
                id="readme",
                type=ResourceType.text,
                name="Project README",
                description="Top-level project documentation",
                content=readme_path.read_text(encoding="utf-8"),
                metadata={"path": str(readme_path)},
                mimeType="text/markdown",
            )
        )

    # 2. Grafana dashboards --------------------------------------------------------------
    dashboards_dir = _BASE_DIR / "grafana" / "dashboards"
    if dashboards_dir.exists():
        for dash_file in dashboards_dir.glob("*.json"):
            resources.append(
                Resource(
                    id=f"dashboard_{dash_file.stem}",
                    type=ResourceType.text,
                    name=f"Grafana dashboard: {dash_file.stem}",
                    description="Grafana dashboard JSON definition",
                    content=dash_file.read_text(encoding="utf-8"),
                    metadata={"path": str(dash_file)},
                    mimeType="application/json",
                )
            )

    # 3. Runbook & guide markdown docs --------------------------------------------------
    docs_dir = _BASE_DIR / "docs"
    if docs_dir.exists():
        # Collect a concise subset instead of dumping every single markdown file
        for doc_file in docs_dir.glob("*.md"):
            # Skip very large docs (>50 KB) to keep payload sizes reasonable
            if doc_file.stat().st_size > 50_000:
                continue

            resources.append(
                Resource(
                    id=f"doc_{doc_file.stem}",
                    type=ResourceType.text,
                    name=f"Documentation: {doc_file.stem.replace('_', ' ').title()}",
                    description="Project documentation markdown file",
                    content=doc_file.read_text(encoding="utf-8"),
                    metadata={"path": str(doc_file)},
                    mimeType="text/markdown",
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
