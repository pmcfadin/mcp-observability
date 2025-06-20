from typing import Any

from fastapi import APIRouter, Depends, Query

from app.clients import AlertManagerClient
from app.security import verify_bearer_token

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
    dependencies=[Depends(verify_bearer_token)],
)


@router.get(
    "/",
    status_code=200,
)
async def get_alerts(
    severity: str | None = Query(None, pattern=r"^[a-zA-Z0-9_-]+$"),
    service: str | None = Query(None, pattern=r"^[a-zA-Z0-9_-]+$"),
    client: AlertManagerClient = Depends(AlertManagerClient),
) -> dict[str, list[dict[str, Any]]]:
    """Return active alerts filtered by optional severity and service labels."""

    active_alerts = await client.fetch_active_alerts(severity, service)
    return {"alerts": active_alerts}
