# Go Observability Guide – MCP Observability

Instrument your Go services with **OpenTelemetry-Go** to emit traces, metrics and logs to mcp-observability.

---

## 1 · Add dependencies

```bash
go get go.opentelemetry.io/otel/sdk@v1.23.0
go get go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp@v1.23.0
go get go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp@v1.23.0
```

---

## 2 · Configure tracer provider & exporter

```go
package main

import (
    "context"
    "log"
    "net/http"

    "go.opentelemetry.io/otel"
    "go.opentelemetry.io/otel/sdk/resource"
    semconv "go.opentelemetry.io/otel/semconv/v1.21.0"
    "go.opentelemetry.io/otel/sdk/trace"
    "go.opentelemetry.io/otel/exporters/otlp/otlptrace/otlptracehttp"
)

func initTracer(ctx context.Context) (*trace.TracerProvider, error) {
    exporter, err := otlptracehttp.New(ctx,
        otlptracehttp.WithEndpoint("otel-collector.observability.svc:4318"),
        otlptracehttp.WithURLPath("/v1/traces"),
        otlptracehttp.WithHeaders(map[string]string{"mcp-token": "<MCP_TOKEN>"}),
        otlptracehttp.WithInsecure(), // or TLS config
    )
    if err != nil { return nil, err }

    tp := trace.NewTracerProvider(
        trace.WithBatcher(exporter),
        trace.WithResource(resource.NewWithAttributes(
            semconv.SchemaURL,
            semconv.ServiceName("my-go-service"),
        )),
    )
    otel.SetTracerProvider(tp)
    return tp, nil
}
```

---

## 3 · Instrument HTTP handlers

```go
import "go.opentelemetry.io/contrib/instrumentation/net/http/otelhttp"

func main() {
    ctx := context.Background()
    tp, err := initTracer(ctx)
    if err != nil { log.Fatal(err) }
    defer tp.Shutdown(ctx)

    mux := http.NewServeMux()
    mux.Handle("/hello", otelhttp.NewHandler(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.Write([]byte("hi"))
    }), "hello"))

    log.Println("listening on :8080")
    if err := http.ListenAndServe(":8080", mux); err != nil {
        log.Fatal(err)
    }
}
```

---

## 4 · Metrics (optional)

Add `go.opentelemetry.io/otel/sdk/metric` and configure an OTLP metrics exporter similarly.

---

## 5 · Validate in Grafana

Search Tempo traces by `service.name="my-go-service"`.

---

## 6 · AI Agent prompt

> "You are an AI Go assistant. Instrument this Go service with OpenTelemetry. Requirements:\n\n* Use `otel/sdk` v1.23+.\n* Send OTLP data to `${OTEL_EXPORTER_OTLP_ENDPOINT}` with header `mcp-token=${MCP_TOKEN}`.\n* Wrap HTTP handlers with `otelhttp.NewHandler`.\n* Add graceful shutdown of the tracer provider."

---

## 7 · Troubleshooting

| Symptom | Cause | Fix |
|---------|------|-----|
| exporter connection refused | Wrong collector address | Verify endpoint reachable from service |
| missing spans | tracer not set | Ensure `otel.SetTracerProvider` called before creating spans | 