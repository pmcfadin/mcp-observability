# MCP Server Security Guide

This document explains how to secure an MCP Observability deployment.

## 1. Bearer-token authentication

All HTTP and gRPC endpoints depend on the `verify_bearer_token` dependency.  The
expected token value is sourced from the `MCP_TOKEN` environment variable.  If
the variable is unset the server refuses every request (`401 Unauthorized`) to
avoid accidental anonymous deployments.

```bash
export MCP_TOKEN="changeme"
```

Pass the token in every request:

```bash
curl -H "Authorization: Bearer changeme" https://mcp.example.com/health
```

## 2. TLS & mutual-TLS

### 2.1 Local development (Docker Compose)

The Compose stack starts a `certgen` sidecar which issues a self-signed CA,
server and client certificates and stores them in the shared `certs/` volume.
`mcp-server` launches Uvicorn with:

```text
--ssl-keyfile /certs/server.key \
--ssl-certfile /certs/server.crt \
--ssl-ca-certs /certs/ca.crt
```

Because a CA bundle is supplied Uvicorn enforces **client authentication**. Use
the generated client certificate to interact with the API:

```bash
curl -H "Authorization: Bearer $MCP_TOKEN" \
     --cert ./certs/client.crt --key ./certs/client.key \
     https://localhost:8000/health
```

### 2.2 Production (Helm / Kubernetes)

Set the following values to enable TLS:

```yaml
mcp:
  tls:
    enabled: true
    certSecret: mcp-server-tls  # Secret must contain server.crt/server.key
    caCertSecret: ca-bundle      # Optional, enables mutual-TLS
```

The container entrypoint automatically adds the appropriate `--ssl-*` flags
when `TLS_ENABLED=1`.

## 3. Network policies

It is strongly recommended to restrict ingress traffic to the MCP service to
trusted clusters or API gateways.

## 4. Secrets management

* Store the bearer token and TLS key material in Kubernetes Secrets or a
  dedicated secret-manager (Vault, AWS Secrets Manager, …).
* Never commit real certificates or tokens to version control.
