# Java / Spring Boot Observability Guide – MCP Observability

Use the **OpenTelemetry Java Agent** to capture traces, metrics and logs from any Spring Boot application with zero code changes.

---

## 1 · Download the Java agent

```bash
curl -L https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v1.35.0/opentelemetry-javaagent.jar -o opentelemetry-javaagent.jar
```

> Pin the version that matches your JVM (Java 8+). Store the JAR alongside your application or fetch it in the Dockerfile.

---

## 2 · Configure JVM flags

```bash
JAVA_TOOL_OPTIONS="-javaagent:/path/opentelemetry-javaagent.jar"
export OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector.observability.svc:4318"
export OTEL_EXPORTER_OTLP_HEADERS="mcp-token=<YOUR_MCP_TOKEN>"
export OTEL_SERVICE_NAME="my-spring-app"
# Optional: enable metrics via Micrometer bridge
export OTEL_METRIC_EXPORT_INTERVAL="60000"
```

You can set these variables in **application.yml**, a `.env` file, or directly in the deployment manifest.

---

## 3 · Dockerfile example

```Dockerfile
FROM eclipse-temurin:21-jre AS base
ENV OTEL_EXPORTER_OTLP_ENDPOINT="http://otel-collector.observability.svc:4318"
ENV OTEL_EXPORTER_OTLP_HEADERS="mcp-token=$MCP_TOKEN"
ENV JAVA_TOOL_OPTIONS="-javaagent:/otel/opentelemetry-javaagent.jar"

# Download agent
ADD https://github.com/open-telemetry/opentelemetry-java-instrumentation/releases/download/v1.35.0/opentelemetry-javaagent.jar /otel/

# Copy Spring Boot fat-jar
COPY target/myapp.jar /app.jar

CMD ["java","-jar","/app.jar"]
```

---

## 4 · Verify data in Grafana

Open your Grafana instance and navigate to:

* *Browse ▸ Traces ▸ Services* – you should see `my-spring-app`.
* *Dashboards ▸ JVM Overview* – metrics like GC pause, thread count.

---

## 5 · AI Agent prompt (copy-paste)

> "You are an AI DevOps assistant. Update the provided Spring Boot project to emit OpenTelemetry telemetry to a remote OTLP endpoint. Requirements:\n\n* Download `opentelemetry-javaagent.jar` version 1.35.0 during build.\n* Pass `-javaagent` JVM flag via `JAVA_TOOL_OPTIONS`.\n* Export environment variables `OTEL_EXPORTER_OTLP_ENDPOINT`, `OTEL_EXPORTER_OTLP_HEADERS` and `OTEL_SERVICE_NAME`.\n* Ensure Micrometer metrics bridge is active.\n* Update `Dockerfile` and `deployment.yaml` with the above.\n* Output a run command example for local testing."

Paste the prompt into your agent to auto-apply the changes.

---

## 6 · Troubleshooting

| Symptom | Check | Fix |
|---------|-------|-----|
| `NoClassDefFoundError` on startup | Path to agent JAR | Verify `JAVA_TOOL_OPTIONS` points to correct file |
| Spans missing | Endpoint & port | Confirm collector is reachable and headers include token |
| High memory | Agent sampling | Adjust `OTEL_TRACES_SAMPLER_ARG` or disable logs | 