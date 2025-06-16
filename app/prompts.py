from __future__ import annotations

from fastapi import APIRouter, status

from mcp_observability.schemas import Prompt

router = APIRouter(tags=["mcp"])

PROMPTS: list[Prompt] = [
    Prompt(
        id="greet",
        template="Hello, {{name}}!",
        inputVariables=["name"],
        metadata={"category": "examples"},
    )
]


@router.get("/prompts", response_model=list[Prompt], status_code=status.HTTP_200_OK)
async def list_prompts() -> list[Prompt]:
    """Return available templated prompts."""

    return PROMPTS 