# React SPA Observability Guide – MCP Observability

Instrument your React single-page application (SPA) with OpenTelemetry to collect client-side performance data and send it to **mcp-observability**.

---

## 1 · Install OpenTelemetry packages

```bash
npm install @opentelemetry/api @opentelemetry/sdk-trace-web @opentelemetry/exporter-trace-otlp-http
```

---

## 2 · Create an instrumentation bootstrap

`src/telemetry.js`:

```js
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { ZoneContextManager } from '@opentelemetry/context-zone';
import { getWebAutoInstrumentations } from '@opentelemetry/auto-instrumentations-web';

const provider = new WebTracerProvider({
  resource: new Resource({ 'service.name': 'my-react-spa' }),
  contextManager: new ZoneContextManager(),
});

provider.addSpanProcessor(
  new BatchSpanProcessor(
    new OTLPTraceExporter({
      url: process.env.REACT_APP_OTEL_EXPORTER_OTLP_ENDPOINT,
      headers: { 'mcp-token': process.env.REACT_APP_MCP_TOKEN },
    })
  )
);

provider.register();

// Enable fetch & XHR instrumentation
getWebAutoInstrumentations({
  // options
});
```

Import this file early in `index.js` before ReactDOM render:

```js
import './telemetry';
import ReactDOM from 'react-dom/client';
// ...rest of bootstrap
```

---

## 3 · Environment variables

Add to `.env`:

```
REACT_APP_OTEL_EXPORTER_OTLP_ENDPOINT=https://mcp.example.com:4318
REACT_APP_MCP_TOKEN=4d3c9f...
```

Ensure variables begin with `REACT_APP_` so Create React App exposes them.

---

## 4 · Verify traces in Grafana Tempo

1. Open Grafana → *Tempo* → search by `service.name="my-react-spa"`.
2. Spans appear for navigations and fetch/XHR calls.

---

## 5 · AI Agent prompt

> "You are an AI front-end assistant. Add OpenTelemetry web instrumentation to the current React SPA. Requirements:\n\n* Use `sdk-trace-web@latest` and OTLP HTTP exporter.\n* Endpoint `${REACT_APP_OTEL_EXPORTER_OTLP_ENDPOINT}` with header `mcp-token=${REACT_APP_MCP_TOKEN}`.\n* Create `src/telemetry.js` and import it before app render.\n* Capture `fetch` and `XMLHttpRequest`."

Paste into your chosen agent to automate the code changes.

---

## 6 · Troubleshooting

| Symptom | Likely cause | Fix |
|---------|--------------|-----|
| `No trace exporter configured` in console | `telemetry.js` imported after ReactDOM render | Ensure import comes first |
| Network errors 403 | Wrong `mcp-token` | Verify token matches `mcp-server` secret |
| CORS preflight fails | Collector endpoint blocking origin | Allow origin or proxy through backend |
