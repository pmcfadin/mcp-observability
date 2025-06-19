from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, HTTPException, Query, status

from app.prompt_store import get_prompt, list_prompts, render_prompt
from mcp_observability.schemas import Prompt

router = APIRouter(tags=["mcp"])


@router.get("/prompts", response_model=List[Prompt], status_code=status.HTTP_200_OK)
async def prompts_list(category: str | None = Query(None)) -> List[Prompt]:
    prompts = list_prompts()
    if category is not None:
        prompts = [p for p in prompts if p.metadata.get("category") == category]
    return prompts


class RenderRequest(Dict[str, str]):  # type: ignore[misc]
    """Ad-hoc request body model: dict of variable -> value."""


@router.post("/prompts/{prompt_id}/render", status_code=status.HTTP_200_OK)
async def prompt_render(prompt_id: str, args: Dict[str, str]) -> Dict[str, str]:
    prompt = get_prompt(prompt_id)
    if prompt is None:
        raise HTTPException(status_code=404, detail="Prompt not found")

    try:
        rendered = render_prompt(prompt, args)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"prompt": rendered}
