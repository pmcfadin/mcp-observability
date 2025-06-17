# Cloud Deployment Guide – MCP Observability

Deploy the **mcp-observability** stack to serverless container platforms such as AWS Fargate, Google Cloud Run, and Azure Container Apps without running your own Kubernetes cluster.

---

## 1 · Prerequisites

* A Docker registry (ECR, Artifact Registry, ACR, Docker Hub)
* Container image: `ghcr.io/your-org/mcp-observability:<tag>` (publish with GH Actions below)
* Secrets / parameters:
  * `MCP_TOKEN` – for API auth
  * `GF_ADMIN_PASSWORD` – Grafana admin password
  * Optional storage creds (e.g. S3 bucket for Loki chunks)

---

## 2 · AWS ECS Fargate (Terraform snippet)

```hcl
module "mcp" {
  source  = "terraform-aws-modules/ecs/aws"
  name    = "mcp"
  capacity_providers = ["FARGATE", "FARGATE_SPOT"]

  container_definitions = [
    {
      name      = "mcp-server"
      image     = "${var.image_repo}:latest"
      cpu       = 256
      memory    = 512
      portMappings = [{ containerPort = 8000, hostPort = 8000 }]
      environment = [
        { name = "MCP_TOKEN", value = var.mcp_token },
      ]
    },
    # Add grafana / loki / etc as sidecars or separate services
  ]
}
```

Expose via an Application Load Balancer module and attach HTTPS.

---

## 3 · Google Cloud Run steps

```bash
gcloud run deploy mcp-server \
  --image gcr.io/$PROJECT_ID/mcp-observability:latest \
  --region us-central1 \
  --platform managed \
  --set-env-vars MCP_TOKEN=$MCP_TOKEN \
  --allow-unauthenticated
```

Use Cloud Storage buckets for Loki if deploying it; remote-write Prometheus to Managed Prometheus.

---

## 4 · Azure Container Apps

```bash
az containerapp create \
  --name mcp-server \
  --image ghcr.io/your-org/mcp-observability:latest \
  --environment prod-env \
  --target-port 8000 \
  --ingress external \
  --env-vars MCP_TOKEN=$MCP_TOKEN
```

Loki can push chunks to Azure Blob Storage; Tempo to Azure Storage.

---

## 5 · GitHub Actions build & push

`.github/workflows/publish.yml`:

```yaml
name: Publish Docker image

on:
  push:
    branches: [main]
    paths:
      - "app/**"
      - "Dockerfile"

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - uses: actions/checkout@v4
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v5
        with:
          context: .
          push: true
          tags: ghcr.io/${{ github.repository }}:${{ github.sha }}
```

---

## 6 · Persistence options

* **Loki** – set `LOKI_CONFIG` to use S3 or GCS object storage.
* **Prometheus** – remote write to Grafana Cloud or Amazon Managed Service for Prometheus.
* **Tempo** – store blocks in S3 / GCS.

If you only need API + Grafana UI, refer to the [Partial Deployment Guide](partial-deployment.md).

---

## 7 · Cost-aware sizing

| Platform | CPU | Memory | Notes |
|----------|-----|--------|-------|
| Fargate Spot | 256m | 512Mi | Cheapest burstable, <$15/mo if idle |
| Cloud Run min instances = 0 | 512m | 512Mi | Pay only per-request |
| Azure CA | 0.5 vCPU | 1Gi | Per-second billing |

Scale vertical resources according to ingest volume.

---

## 8 · AI Agent prompt

> "You are an AI DevOps agent. Deploy mcp-observability mcp-server and Grafana to AWS Fargate. Requirements:\n\n* Build image from `Dockerfile` in repo; push to ECR.\n* Provision task definitions with env vars `MCP_TOKEN`, `GF_ADMIN_PASSWORD`.\n* Expose ALB HTTPS with ACM cert.\n* Attach Spot capacity where possible."

--- 