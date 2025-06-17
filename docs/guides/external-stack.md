# Deploying MCP Observability in an Existing Environment

Already have Prometheus, Loki, Tempo and Grafana running?  Great!  This document explains how to drop the **`mcp-observability`** container into that ecosystem and expose a unified AI-friendly API without touching your current stack.

---

## 1 · Network + Permissions checklist

| Requirement | Notes |
| ----------- | ----- |
| Outgoing HTTPS (or HTTP) access from the MCP container to **Loki, Prometheus, Tempo, Alertmanager** | Default ports 3100, 9090, 3200, 9093. Adjust if you expose custom LoadBalancers/Ingress. |
| Bearer-token or mTLS secret storage | MCP needs its own `MCP_TOKEN`; optionally server TLS key/cert. |
| Kubernetes ServiceAccount (if Helm) | No cluster-wide RBAC needed: only egress to existing services. |

---

## 2 · Docker-run quick start

```bash
docker run -d --name mcp-server \
  -e MCP_TOKEN=changeme \
  -e LOKI_BASE_URL=https://loki.prod.mycorp:3100 \
  -e PROMETHEUS_BASE_URL=https://prom.prod.mycorp:9090 \
  -e TEMPO_BASE_URL=https://tempo.prod.mycorp:3200 \
  -e ALERTMANAGER_BASE_URL=https://prom.prod.mycorp:9093/alertmanager \
  -p 8081:8000 docker.io/pmcfadin/mcp-observability:latest
```

*Exposes HTTP on port 8081.*  Verify:

```bash
curl -H "Authorization: Bearer changeme" http://localhost:8081/health
```

### 2.1 Enabling TLS / mutual-TLS on the API

```bash
# server.crt / server.key issued by your PKI
# ca.crt = CA bundle trusted by clients

docker run -d --name mcp-server \
  -e MCP_TOKEN=changeme \
  -e TLS_ENABLED=1 \
  -v $PWD/tls/server.crt:/certs/server.crt:ro \
  -v $PWD/tls/server.key:/certs/server.key:ro \
  -v $PWD/tls/ca.crt:/certs/ca.crt:ro \
  -e LOKI_BASE_URL=… -e PROMETHEUS_BASE_URL=… (etc.) \
  -p 8443:8000 docker.io/pmcfadin/mcp-observability:latest
```

If you **omit** `ca.crt`, clients can connect with ordinary HTTPS.
If you **include** it, MCP requires mutual-TLS (client cert signed by that CA).

---

## 3 · Helm chart integration

*(Assumes you already have Prom/Loki/Tempo in the same namespace or reachable via DNS.)*

```bash
helm repo add my-mcp https://ghcr.io/<you>/charts
helm install mcp-obs my-mcp/mcp-observability \
  --set mcpServer.token=changeme \
  --set mcpServer.extraEnv={LOKI_BASE_URL=https://loki.monitoring.svc.cluster.local:3100} \
  --set mcpServer.tls.enabled=true \
  --set mcpServer.tls.certSecret=mcp-server-tls \
  --set mcpServer.tls.caCertSecret=ca-bundle
```

Values explained:

| Key | Purpose |
| --- | ------- |
| `mcpServer.token` | Bearer-token for all API calls |
| `mcpServer.extraEnv` | Any of `*_BASE_URL` overrides |
| `mcpServer.tls.enabled` | Turn on HTTPS inside the pod |
| `*.certSecret` | Kubernetes Secret containing `server.crt`, `server.key` |

---

## 4 · Common production scenarios

### Scenario A – SRE ChatOps bot

1. Bot receives "site slow" Slack alert.
2. Calls `GET /metrics/latency?percentile=0.99&window=5m&service=api-gw`.
3. Latency spike confirmed → bot fetches `/logs/errors` and `/alerts` to gather context.
4. Posts a threaded summary in Slack linking to Grafana trace.

### Scenario B – CI performance gate

* Pipeline stage runs a load-test, then: *

```bash
p95=$(curl -s -H "Authorization: Bearer $MCP_TOKEN" \
           "$MCP_API_URL/metrics/latency?percentile=0.95&window=3m" | jq .latency_seconds)
if (( $(echo "$p95 > 0.15" | bc -l) )); then
  echo "🛑 p95 latency too high ($p95 s)"; exit 1
fi
```

### Scenario C – Incident post-mortem

```bash
# Fetch all ERROR-level logs for a timeframe
tar zcvf errors.tgz <(curl …/logs/errors?limit=1000&range=2h | jq -r .logs[])

# Grab traces by IDs from the logs
tempo_ids=$(grep -oE '[a-f0-9]{32}' errors.tgz | sort -u)
for id in $tempo_ids; do
  curl …/traces/$id -o traces/$id.json
  curl …/traces/$id/logs -o traces/$id-logs.json
done
```

Everything needed for the write-up is fetched programmatically via the MCP API, without direct Prom/Loki/Tempo access for analysts.

---

## 5 · Troubleshooting tips

| Symptom | Resolution |
| ------- | ---------- |
| `502 Bad Gateway` from MCP | Check the target `*_BASE_URL`; ensure service is reachable from the pod/container. |
| `401 Unauthorized` | Did you pass `Authorization: Bearer $MCP_TOKEN`? Is the env var set in the container? |
| Mutual-TLS handshake fails | Verify client certificate is signed by same CA as `ca.crt`; check time-skew. |
| Slow queries | Loki label cardinality, Prometheus remote-read latency – MCP just forwards the query. |

---

## 6 · Next steps

* Automate image pulls via GitHub Actions or ArgoCD.
* Add Prometheus alert rules that fire when MCP endpoints start timing out.
* Configure Grafana dashboards (JSON files in `grafana/dashboards/`) to point at your real data sources. 