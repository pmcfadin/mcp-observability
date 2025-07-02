# Next.js Observability Guide – Sending Telemetry to MCP Observability

Instrument your React / Next.js application with **OpenTelemetry JS** and forward data to the Docker Compose stack.

---

## 1 · Install client-side packages

```bash
npm install @opentelemetry/api @opentelemetry/sdk-trace-web @opentelemetry/sdk-trace-base @opentelemetry/exporter-trace-otlp-http
```

For server-side instrumentation (getServerSideProps, API routes):

```bash
npm install @opentelemetry/sdk-node @opentelemetry/auto-instrumentations-node
```

---

## 2 · Configure the OTLP exporter (browser)

Create `lib/otel.ts`:

```ts
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { SimpleSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { trace } from '@opentelemetry/api';

// 1. Provider & exporter
const provider = new WebTracerProvider();
provider.addSpanProcessor(
  new SimpleSpanProcessor(
    new OTLPTraceExporter({ url: 'http://localhost:4318/v1/traces' })
  )
);
provider.register();

export const tracer = trace.getTracer('nextjs-frontend');
```

Call this file once during app bootstrap (e.g., `_app.tsx`):

```ts
if (typeof window !== 'undefined') {
  // eslint-disable-next-line @typescript-eslint/no-var-requires
  require('../lib/otel');
}
```

---

## 3 · Record spans

```ts
import { tracer } from '../lib/otel';

export default function Home() {
  const handleClick = () => {
    const span = tracer.startSpan('button-click');
    // do work…
    span.end();
  };
  return <button onClick={handleClick}>Click me</button>;
}
```

---

## 4 · Server-side instrumentation

Create `server-otel.ts` in project root:

```ts
import { NodeSDK } from '@opentelemetry/sdk-node';
import { getNodeAutoInstrumentations } from '@opentelemetry/auto-instrumentations-node';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';

const sdk = new NodeSDK({
  traceExporter: new OTLPTraceExporter({ url: 'http://otel-collector:4318/v1/traces' }),
  instrumentations: [getNodeAutoInstrumentations()],
});

sdk.start();
```

Import this file at the top of `next.config.js` or the custom server entry to ensure it runs before your app code.

---

## 5 · Environment variables

For containerized deployments set:

```bash
OTEL_EXPORTER_OTLP_ENDPOINT=http://otel-collector:4318
OTEL_SERVICE_NAME=nextjs-frontend
```

---

## 6 · Visualise in Grafana

Use the *Tempo / Jaeger* data source in Grafana (pre-configured) to see spans and trace waterfalls. Metrics (e.g., Web Vitals) can be forwarded via OTLP metrics exporter in a similar fashion.

---

## 7 · Troubleshooting

* **CORS errors** – the collector container listens on `0.0.0.0` and includes permissive CORS headers. If you proxy via nginx/etc., ensure CORS is propagated.
* **Large bundle size** – load OTLP libraries dynamically or leverage tree-shaking to keep the client bundle small.
