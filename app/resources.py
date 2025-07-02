from __future__ import annotations

import asyncio
from typing import List

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse

from app.resource_store import get_resource, list_resources, list_templates
from mcp_observability.schemas import Resource, ResourcePage

router = APIRouter(tags=["mcp"])


@router.get(
    "/resources",
    response_model=ResourcePage,
    status_code=status.HTTP_200_OK,
)
async def resources_list(
    limit: int = Query(20, ge=1, le=100),
    cursor: int = Query(0, ge=0),
) -> ResourcePage:
    """List resources with offset/limit pagination.

    * `cursor` is a zero-based offset into the full resource list.
    * `limit` caps the number of items returned.
    * The response includes `nextCursor` when further pages exist.
    """

    all_res = list_resources()
    page_items: List[Resource] = all_res[cursor : cursor + limit]
    next_cursor = cursor + limit if cursor + limit < len(all_res) else None
    return ResourcePage(
        resources=page_items,
        templates=list_templates() if cursor == 0 else None,
        next_cursor=next_cursor,
    )


@router.get(
    "/resources/{resource_id}",
    response_model=Resource,
    status_code=status.HTTP_200_OK,
)
async def resource_read(resource_id: str) -> Resource:
    res = get_resource(resource_id)
    if res is None:
        raise HTTPException(status_code=404, detail="Resource not found")
    return res


@router.get("/resources/subscribe")
async def resources_subscribe():
    """Very simple Server-Sent Events stream for resource change notifications.

    This MVP sends a periodic ping every 15 s.  In a future iteration the
    store can publish events when resources are added/updated.
    """

    async def event_generator():
        while True:
            # Comment lines are ignored by EventSource clients but keep the
            # connection alive across proxies.
            yield "\n"
            await asyncio.sleep(15)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
