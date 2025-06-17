# MCP Observability

**MCP Observability** gives your AI agents—and you—a single HTTPS endpoint to explore logs, metrics and traces for any application, without learning half-a-dozen vendor APIs.

•   Standards-based: OpenTelemetry ingestion, Grafana/Loki/Tempo storage  
•   AI-ready: implements the Model-Context-Protocol (MCP) so agents can ask natural-language questions about performance issues  
•   Zero-lock-in: self-host via Docker Compose, Kubernetes (Helm) or any cloud container platform

---

## 1 · Why would I use this?

Imagine asking your favourite coding agent:

> "The /checkout endpoint went 💥 at 09:33 UTC. Why?"

The agent queries the MCP endpoint, pulls traces, error logs and latency metrics, and replies with an RCA—and a pull-request suggestion.  **That** is what this repo enables.

---

## 2 · How do I run it?

Choose the deployment style that fits you:

| Environment | Quick start | Full guide |
|-------------|------------|------------|
| Local laptop | `docker compose -f mcp-obs.yml up -d` | [Docker guide](docs/guides/docker.md) |
| Kubernetes   | `helm install mcp charts/mcp-obs`      | [Kubernetes & Helm](docs/guides/kubernetes.md) |
| Cloud (ECS, Cloud Run, Azure CA) | see Terraform/CLI snippets | [Cloud deployment](docs/guides/cloud-deployment.md) |

After the stack is up:

```bash
export MCP_TOKEN="$(openssl rand -hex 16)"   # use the same token you passed during install

# Health check
curl -k -H "Authorization: Bearer $MCP_TOKEN" https://<HOST>:8000/health
```

Open Grafana at `https://<HOST>:3000` (admin / $GF_ADMIN_PASSWORD) to browse dashboards.

---

## 3 · Talking to the MCP endpoint

All requests are HTTPS + Bearer-token.  Key endpoints:

| Path | What it's for |
|------|---------------|
| `/logs/errors?limit=100` | Latest error logs from Loki |
| `/metrics/latency?percentile=0.95` | 95-th percentile latency from Prometheus |
| `/resources` | Metadata describing the data sources your agent can query |
| `/prompts` | Parameterised prompt templates you can re-use |

### Example agent prompt

> "Retrieve the top three slowest routes over the last hour and suggest an optimisation."

that becomes an MCP `SamplingRequest` under the hood; the server stitches data from Prometheus & Tempo and returns JSON your agent can read.

---

## 4 · Instrumenting your application

Pick your language guide and drop in the ready-made snippet:

* Python & FastAPI – [docs/observability/python_fastapi.md](docs/observability/python_fastapi.md)
* Java / Spring Boot – [docs/observability/java_spring.md](docs/observability/java_spring.md)
* Node.js – [docs/observability/nodejs.md](docs/observability/nodejs.md)
* Go – [docs/observability/go.md](docs/observability/go.md)
* Next.js & React SPA – see the respective frontend guides

Need only a subset (e.g. logs-only)?  Use the [Partial-deployment guide](docs/guides/partial-deployment.md).

---

## 5 · Security in two minutes

1.  **Bearer token** – set `MCP_TOKEN` in your deployment and pass it in `Authorization` headers.
2.  **TLS** – self-signed by default (dev), or plug in cert-manager / ACM / Cloud CA.
3.  **mTLS (optional)** – enable client cert auth by mounting your CA & toggling `security.mtls=true` in `values.yaml`.

---

## 6 · Troubleshooting cheatsheet

| Symptom | Check | Fix |
|---------|-------|-----|
| `401 Unauthorized` | Correct token? | Pass `-H "Authorization: Bearer $MCP_TOKEN"` |
| No traces showing | Otel-collector healthy? Endpoint URL correct in client? | Verify port 4318 reachable |
| Grafana empty dashboards | Components disabled | See [Partial deployment](docs/guides/partial-deployment.md) |

---

## 7 · I want to hack on the code!

Fantastic 🎉 — head over to **[docs/contributing](docs/contributing/)** for architecture diagrams, dev-environment setup, and the contributor workflow.  The README you're reading will stay laser-focused on **users** and **agents**.
