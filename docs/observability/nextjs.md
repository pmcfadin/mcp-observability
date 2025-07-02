# Next.js Observability Guide – MCP Observability

Collect performance metrics and traces from both the browser and the server-side runtime of your **Next.js** app.

---

## 1 · Install dependencies

```bash
npm install @opentelemetry/api @opentelemetry/sdk-trace-web @opentelemetry/sdk-trace-node @opentelemetry/exporter-trace-otlp-http next-otel
```

---

## 2 · Instrument client-side (Web Vitals)

Create `src/otel/web.js`:

```js
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { SimpleSpanProcessor } from '@opentelemetry/sdk-trace-web';

const provider = new WebTracerProvider();
provider.addSpanProcessor(
  new SimpleSpanProcessor(
    new OTLPTraceExporter({
      url: process.env.NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT,
      headers: { 'mcp-token': process.env.NEXT_PUBLIC_MCP_TOKEN },
    })
  )
);
provider.register();
```

import it in `_app.tsx`:

```ts
if (typeof window !== 'undefined') {
  import('../otel/web');
}
```

---

## 3 · Instrument server runtime

Create `otel.server.js` in project root:

```js
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT,
    headers: { 'mcp-token': process.env.MCP_TOKEN },
  }),
});

sdk.start();
```

Add to `server.js` or custom `next start` entry point:

```js
require('./otel.server');
const next = require('next');
// ... your Next.js server code
```

---

## 4 · Environment variables

| Variable | Example |
|----------|---------|
| NEXT_PUBLIC_OTEL_EXPORTER_OTLP_ENDPOINT | https://mcp.example.com:4318 |
| NEXT_PUBLIC_MCP_TOKEN | 4d3c9f... |
| OTEL_EXPORTER_OTLP_ENDPOINT | http://otel-collector.observability.svc:4318 |
| MCP_TOKEN | 4d3c9f... |

---

## 5 · Verify in Grafana

1. Open *Explore* and query `trace_id` to see client→server spans.
2. Dashboards ▸ *Web Vitals* will show FCP, LCP, CLS if you export them as metrics.

---

## 6 · AI Agent prompt

> "You are an AI coding agent. Instrument the current Next.js app with OpenTelemetry on both client and server. Requirements:\n\n* Use `next-otel` if available, otherwise manual setup.\n* Export to `${OTEL_EXPORTER_OTLP_ENDPOINT}` with `${MCP_TOKEN}` header.\n* Capture web vitals and API route traces.\n* Update `Dockerfile` and `Vercel` env vars."

Paste into Cursor or Claude to auto-modify your repo.

---

## 7 · Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `ReferenceError: window` during build | Client tracer imported on server | Import only in browser (see `_app.tsx`) |
| Spans dropped | CORS block | Add OTLP endpoint domain to allowed origins |
