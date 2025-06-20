from typing import Any, List

import httpx
from fastapi import Depends, HTTPException, status

from app.config import Settings, get_settings


class LokiClient:
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.base_url = settings.LOKI_BASE_URL
        self.timeout = settings.DEFAULT_HTTP_TIMEOUT

    async def _query(self, query: str, limit: int = 1000) -> List[str]:
        url = f"{self.base_url.rstrip('/')}/loki/api/v1/query"
        params = {"query": query, "limit": str(limit)}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to contact Loki: {exc}",
                ) from exc

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Loki returned {response.status_code}",
            )

        data: Any = response.json()
        try:
            results = data["data"]["result"]
        except (KeyError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unexpected Loki response format",
            ) from exc

        lines: List[str] = []
        for stream in results:
            for _ts, line in stream.get("values", []):
                lines.append(line)
        return lines

    async def fetch_error_logs(
        self, limit: int, service: str | None = None, time_range: str | None = None
    ) -> List[str]:
        selector = '{level="error"}'
        if service:
            selector = f'{{level="error",service="{service}"}}'
        query_str = f"{selector}[{time_range}]" if time_range else selector
        return await self._query(query_str, limit)

    async def search_logs(
        self, query: str, service: str | None, time_range: str | None
    ) -> list[str]:
        selector = "{}"
        if service:
            selector = f'{{service="{service}"}}'
        logql = f'{selector} |= "{query}"'
        if time_range:
            logql = f"{logql}[{time_range}]"
        return await self._query(logql)

    async def fetch_trace_logs(self, trace_id: str, limit: int) -> list[str]:
        query = f'{{trace_id="{trace_id}"}}'
        return await self._query(query, limit)


class PrometheusClient:
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.base_url = settings.PROMETHEUS_BASE_URL
        self.timeout = settings.DEFAULT_HTTP_TIMEOUT

    async def _query(self, promql: str) -> Any:
        url = f"{self.base_url.rstrip('/')}/api/v1/query"
        params = {"query": promql}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url, params=params)
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to contact Prometheus: {exc}",
                ) from exc

        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Prometheus returned {response.status_code}",
            )
        data: Any = response.json()
        try:
            return data["data"]["result"]
        except (KeyError, TypeError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unexpected Prometheus response format",
            ) from exc

    async def fetch_latency_percentile(
        self, percentile: float, window: str, service: str | None = None
    ) -> float:
        metric = "http_server_request_duration_seconds_bucket"
        if service:
            metric = f'{metric}{{service="{service}"}}'
        promql = (
            f"histogram_quantile({percentile}, sum(rate({metric}[{window}])) by (le))"
        )
        result = await self._query(promql)
        try:
            return float(result[0]["value"][1])
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Unexpected Prometheus response format or non-numeric value",
            ) from exc

    async def execute_promql(self, promql: str) -> Any:
        return await self._query(promql)


class TempoClient:
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.base_url = settings.TEMPO_BASE_URL
        self.timeout = settings.DEFAULT_HTTP_TIMEOUT

    async def fetch_trace_json(self, trace_id: str) -> Any:
        url = f"{self.base_url.rstrip('/')}/api/traces/{trace_id}"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.get(url)
            except httpx.HTTPError as exc:
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Failed to contact Tempo: {exc}",
                ) from exc
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"Tempo returned {response.status_code}",
            )
        return response.json()


class AlertManagerClient:
    def __init__(self, settings: Settings = Depends(get_settings)):
        self.base_url = settings.ALERTMANAGER_BASE_URL
        self.timeout = settings.DEFAULT_HTTP_TIMEOUT

    async def fetch_active_alerts(
        self, severity: str | None = None, service: str | None = None
    ) -> list[dict[str, Any]]:
        url = f"{self.base_url.rstrip('/')}/api/v2/alerts"
        async with httpx.AsyncClient(timeout=self.timeout) as client:
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
