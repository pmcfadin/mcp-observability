# Node.js Observability Guide – MCP Observability

Instrument any Node backend (Express, NestJS, Fastify, etc.) using the **OpenTelemetry Node SDK**.

---

## 1 · Install packages

```bash
npm install @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node @opentelemetry/exporter-trace-otlp-http
```

---

## 2 · Create the SDK bootstrap

`otel.js` (require this before your server starts):

```js
const { NodeSDK } = require('@opentelemetry/sdk-node');
const { getNodeAutoInstrumentations } = require('@opentelemetry/auto-instrumentations-node');
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-http');

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({
    url: process.env.OTEL_EXPORTER_OTLP_ENDPOINT,
    headers: { 'mcp-token': process.env.MCP_TOKEN },
  }),
  serviceName: process.env.OTEL_SERVICE_NAME || 'my-node-app',
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start().then(() => console.log('OTEL SDK started')).catch(console.error);
```

---

## 3 · Modify your entry point

For **Express** in `index.js`:

```js
require('./otel'); // start telemetry first

const express = require('express');
const app = express();

app.get('/hello', (req, res) => {
  res.send('hello');
});

app.listen(3000);
```

---

## 4 · Environment variables

```
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector.observability.svc:4318
MCP_TOKEN=4d3c9f...
OTEL_SERVICE_NAME=my-node-app
```

---

## 5 · Validate in Grafana Tempo

Query by `service.name="my-node-app"` under *Traces ▸ Services*.

---

## 6 · AI Agent prompt

> "You are an AI Node.js assistant. Add OpenTelemetry Node SDK auto-instrumentation to this project. Requirements:\n\n* Use `@opentelemetry/sdk-node` and auto-instrumentations.\n* Export to `${OTEL_EXPORTER_OTLP_ENDPOINT}` with header `mcp-token=${MCP_TOKEN}`.\n* Wrap the startup script with `require('./otel.js')`."

---

## 7 · Troubleshooting

| Symptom | Cause | Fix |
|---------|------|-----|
| `DiagConsoleLogger` warns exporter unreachable | Wrong URL/firewall | Verify collector endpoint & port 4318 open |
| No spans for DB queries | Package not auto-instrumented | Import specific instrumentation package (e.g. `@opentelemetry/instrumentation-mongodb`) | 