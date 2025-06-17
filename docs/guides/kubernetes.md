# Kubernetes Getting Started – MCP Observability

Run **MCP Observability** in any Kubernetes cluster using the provided Helm chart. This guide covers installing the full observability stack or just the API server.

---

## 1 · Prerequisites

* Kubernetes 1.26+
* `kubectl` configured with context pointing to your cluster
* Helm v3.12+
* (Optional) cert-manager if you prefer automated TLS certificates other than the default self-signed setup

---

## 2 · Clone & update chart dependencies

```bash
git clone https://github.com/your-org/mcp-observability.git
cd mcp-observability
helm dependency update charts/mcp-obs
```

---

## 3 · Choose a deployment mode

| Mode | Components installed | Command snippet |
|------|----------------------|-----------------|
| **Full stack** | mcp-server + Grafana + Prometheus + Loki + Tempo + Otel-Collector | `helm install mcp charts/mcp-obs` |
| **Server only** | Just the API (for clusters that already provide Prom/Loki etc.) | `helm install mcp charts/mcp-obs --set grafana.enabled=false,loki.enabled=false,prometheus.enabled=false,tempo.enabled=false` |

---

## 4 · Configure secrets & persistence (recommended)

Create a namespace and a strong `MCP_TOKEN` secret:

```bash
NAMESPACE="observability"
TOKEN="$(openssl rand -hex 16)"

kubectl create namespace $NAMESPACE
kubectl create secret generic mcp-token -n $NAMESPACE \
  --from-literal=token="$TOKEN"
```

Then install with overrides:

```bash
helm install mcp charts/mcp-obs \
  -n $NAMESPACE \
  --set mcpServer.env.MCP_TOKEN=$TOKEN \
  --set grafana.persistence.enabled=true \
  --set loki.persistence.enabled=true \
  --set prometheus.server.persistentVolume.enabled=true \
  --set tempo.persistence.enabled=true
```

The chart automatically creates a self-signed TLS certificate via cert-manager. Override issuer or disable TLS through `values.yaml` if desired.

## 4.1 · Custom TLS issuer

If your cluster already runs cert-manager with a ClusterIssuer (e.g. Let's Encrypt), override the issuer like so:

```yaml
# tls-issuer-values.yaml
mcpServer:
  tls:
    enabled: true
    issuer:
      kind: ClusterIssuer
      name: letsencrypt-prod
```

Install with:

```bash
helm install mcp charts/mcp-obs -n $NAMESPACE -f tls-issuer-values.yaml
```

## 4.2 · Resource limits & requests

All sub-charts expose `resources` blocks. Example minimal limits:

```yaml
# resources-values.yaml
mcpServer:
  resources:
    limits:
      cpu: 500m
      memory: 512Mi
    requests:
      cpu: 100m
      memory: 128Mi
prometheus:
  server:
    resources:
      limits:
        cpu: 1
        memory: 2Gi
```

Apply with `-f resources-values.yaml` during installation or upgrade.

## 4.3 · Enable / disable components individually

Set the `enabled` flag under each top-level chart key (`grafana`, `loki`, `prometheus`, `tempo`, `otelCollector`). For example, API server with Grafana **only**:

```bash
helm install mcp charts/mcp-obs -n $NAMESPACE \
  --set grafana.enabled=true \
  --set prometheus.enabled=false \
  --set loki.enabled=false \
  --set tempo.enabled=false \
  --set otelCollector.enabled=false
```

A full list of flags is documented in `charts/mcp-obs/values.yaml`.

---

## 5 · Accessing the services

By default, the chart exposes **ClusterIP** services. Use one of:

1. **Port-forwarding** (quickest):

   ```bash
   kubectl -n $NAMESPACE port-forward svc/mcp-obs-grafana 3000:80 &
   kubectl -n $NAMESPACE port-forward svc/mcp-obs-server 8000:8000 &
   ```

2. **Ingress**: supply your own Ingress or enable the Ingress block in `values.yaml`.

3. **LoadBalancer**: change `service.type` for Grafana / mcp-server to `LoadBalancer` in your overrides file.

---

## 6 · Verify deployment

```bash
# Health check
curl -k -H "Authorization: Bearer $TOKEN" https://<SERVER_HOST>:8000/health

# Grafana
open http://localhost:3000  # if port-forwarded
```

Grafana admin credentials default to `admin / admin` unless overridden with `grafana.adminPassword` in values.

---

## 7 · Upgrading & uninstalling

```bash
# Upgrade (pulls new images / chart version)
helm upgrade mcp charts/mcp-obs -n $NAMESPACE

# Uninstall
helm uninstall mcp -n $NAMESPACE
```

PersistentVolumeClaims created by sub-charts are **not** deleted automatically; remove them manually if needed.

---

## 8 · Troubleshooting

* `helm install` hangs – check that the dependent charts were downloaded (`charts/` directory populated).
* Pods in CrashLoopBackOff – run `kubectl logs` on the failing pod; verify secrets and image pulls.
* TLS errors – disable TLS (`--set tls.enabled=false`) for testing, or configure an external issuer.

## 8.1 · Troubleshooting CRDs & PV binding

* **CRDs not installed** – ensure you run `helm dependency update charts/mcp-obs`; sub-charts such as Loki ship CRDs that Helm must apply.
* **PVC stuck in Pending** – confirm your cluster has a default StorageClass and enough capacity; list classes with `kubectl get sc`. 