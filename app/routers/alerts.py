import os
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.security import verify_bearer_token

router = APIRouter(
    prefix="/alerts",
    tags=["alerts"],
    dependencies=[Depends(verify_bearer_token)],
)

ALERTMANAGER_BASE_URL: str = os.getenv(
    "ALERTMANAGER_BASE_URL", "http://alertmanager:9093"
)


async def _fetch_active_alerts(
    severity: str | None = None, service: str | None = None
) -> list[dict[str, Any]]:
    """Fetch active alerts from Alertmanager and filter by severity/service if given."""

    url = f"{ALERTMANAGER_BASE_URL.rstrip('/')}/api/v2/alerts"

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            response = await client.get(url)
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Failed to contact Alertmanager: {exc}",
            ) from exc

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Alertmanager returned {response.status_code}",
        )

    alerts: Any = response.json()
    if not isinstance(alerts, list):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unexpected Alertmanager response format",
        )

    def _matches(alert: dict[str, Any]) -> bool:
        labels = alert.get("labels", {})
        if severity and labels.get("severity") != severity:
            return False
        if service and labels.get("service") != service:
            return False
        return True

    return [a for a in alerts if _matches(a)]


@router.get(
    "/",
    status_code=status.HTTP_200_OK,
)
async def get_alerts(
    severity: str | None = Query(None, pattern=r"^[a-zA-Z0-9_-]+$"),
    service: str | None = Query(None, pattern=r"^[a-zA-Z0-9_-]+$"),
) -> dict[str, list[dict[str, Any]]]:
    """Return active alerts filtered by optional severity and service labels."""

    active_alerts = await _fetch_active_alerts(severity, service)
    return {"alerts": active_alerts}
