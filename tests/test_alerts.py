import pytest
from httpx import ASGITransport, AsyncClient

from app.clients import AlertManagerClient
from app.main import app


@pytest.mark.asyncio
async def test_alerts_endpoint(monkeypatch: pytest.MonkeyPatch):
    alerts_json = [
        {"labels": {"alertname": "HighCPU", "severity": "critical", "service": "api"}}
    ]

    class MockAlertManagerClient:
        async def fetch_active_alerts(
            self, severity: str | None = None, service: str | None = None
        ):
            return alerts_json

    app.dependency_overrides[AlertManagerClient] = MockAlertManagerClient

    monkeypatch.setenv("MCP_TOKEN", "testtoken")

    transport = ASGITransport(app=app, raise_app_exceptions=True)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/alerts/?severity=critical&service=api",
            headers={"Authorization": "Bearer testtoken"},
        )

    assert resp.status_code == 200
    assert resp.json() == {"alerts": alerts_json}

    del app.dependency_overrides[AlertManagerClient]
