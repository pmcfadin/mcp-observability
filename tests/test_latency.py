import os
import time
from statistics import quantiles

from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app

TOKEN = "secret"


def test_health_latency_p95_under_150ms() -> None:
    os.environ["MCP_TOKEN"] = TOKEN
    get_settings.cache_clear()
    client = TestClient(app)

    durations: list[float] = []
    headers = {"Authorization": f"Bearer {TOKEN}"}

    for _ in range(100):
        start = time.perf_counter()
        resp = client.get("/health", headers=headers)
        assert resp.status_code == 200
        durations.append(time.perf_counter() - start)

    # Calculate 95th percentile using inclusive method
    p95 = sorted(durations)[int(0.95 * len(durations)) - 1]
    assert p95 < 0.15, f"p95 latency {p95:.3f}s exceeds 150ms"
