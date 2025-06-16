from __future__ import annotations

from fastapi import APIRouter, status
from pathlib import Path

from mcp_observability.schemas import Resource, ResourceType

router = APIRouter(tags=["mcp"])

# Example in-memory resources; in a real deployment this could be backed by a
# database or fetched dynamically from connected systems.  IDs should be
# unique within the server scope.
_readme_path = Path(__file__).resolve().parent.parent / "README.md"
try:
    _readme_text = _readme_path.read_text(encoding="utf-8")
except FileNotFoundError:
    _readme_text = ""

RESOURCES: list[Resource] = [
    Resource(
        id="readme",
        type=ResourceType.text,
        name="Project README",
        description="Top-level project documentation",
        content=_readme_text,
        metadata={"path": str(_readme_path)},
    )
]


@router.get("/resources", response_model=list[Resource], status_code=status.HTTP_200_OK)
async def list_resources() -> list[Resource]:
    """Return metadata for all available Resources.

    The endpoint intentionally *does not* return the resource *content* unless
    it is embedded in the model (e.g. small text).  Large or binary content
    SHOULD be provided via an external `content` reference (URL or file path)
    or through a dedicated download endpoint.  For this MVP we only expose the
    meta layer.
    """

    return RESOURCES 