import pytest
from httpx import Response
from pytest_httpx import HTTPXMock

from app.clients import AlertManagerClient
from app.main import app


@pytest.mark.asyncio
async def test_alerts_endpoint(httpx_mock: HTTPXMock):
    alerts_json = [
        {"labels": {"alertname": "HighCPU", "severity": "critical", "service": "api"}}
    ]
    httpx_mock.add_response(
        url="http://alertmanager:9093/api/v2/alerts",
        json=alerts_json,
    )

    client = AlertManagerClient()
    alerts = await client.fetch_active_alerts(severity="critical", service="api")

    assert alerts == alerts_json
