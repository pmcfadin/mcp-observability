import pytest
from pytest_httpx import HTTPXMock

from app.clients import AlertManagerClient
from app.main import app

pytestmark = pytest.mark.httpx_mock(assert_all_responses_were_requested=False)


@pytest.mark.asyncio
async def test_alerts_endpoint(httpx_mock: HTTPXMock):
    alerts_json = [
        {"labels": {"alertname": "HighCPU", "severity": "critical", "service": "api"}}
    ]
    httpx_mock.add_response(json=alerts_json, is_optional=True)

    client = AlertManagerClient()
    alerts = await client.fetch_active_alerts(severity="critical", service="api")

    assert alerts == alerts_json
