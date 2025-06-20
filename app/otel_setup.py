from __future__ import annotations

"""OpenTelemetry configuration for MCP service.

This module provides `configure_opentelemetry(app)` which instruments the
FastAPI *app* with tracing (and, in future, metrics) using the OpenTelemetry
SDK. By default, spans are exported via OTLP to the endpoint indicated by the
``OTEL_EXPORTER_OTLP_ENDPOINT`` environment variable (falls back to
``http://otel-collector:4318`` when unset).

The helper supports injection of a custom ``span_exporter`` to simplify unit
testing with the ``InMemorySpanExporter`` provided by
``opentelemetry-sdk.testing``.
"""

import os
from typing import Optional

from fastapi import FastAPI

# OpenTelemetry core
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Instrumentations
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

# The exporter families are imported lazily inside ``configure_opentelemetry``
# based on the configured endpoint (gRPC vs HTTP). This avoids unnecessary
# imports in environments where only one transport is desired.

__all__ = ["configure_opentelemetry"]


def _create_default_exporter(endpoint: str):  # pylint: disable=import-outside-toplevel
    """Return an OTLP span exporter suitable for *endpoint*.

    If the endpoint begins with ``http://`` or ``https://``, an HTTP OTLP
    exporter is used. Otherwise, the gRPC exporter is selected. The caller is
    responsible for ensuring compatibility with the target collector.
    """

    if endpoint.startswith(("http://", "https://")):
        # HTTP/protobuf exporter
        return OTLPSpanExporter(endpoint=endpoint)

    # Default gRPC exporter (no scheme)
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
        OTLPSpanExporter as OTLPGRPCSpanExporter,
    )

    # gRPC exporter uses TLS unless ``insecure`` is True. We assume an internal
    # collector, so using insecure transport is fine here.
    return OTLPGRPCSpanExporter(endpoint=endpoint, insecure=True)


def configure_opentelemetry(
    app: FastAPI,
    *,
    span_exporter=None,
    use_simple_processor: bool = False,
    reconfigure: bool = False,
) -> None:
    """Configure tracing for *app* if not already configured.

    Args:
        app: The FastAPI application to instrument.
        span_exporter: Optional *SpanExporter* instance. When omitted, an OTLP
            exporter is created based on environment variables.
        use_simple_processor: When *True*, a ``SimpleSpanProcessor`` is used in
            place of the default ``BatchSpanProcessor``. This is handy for
            deterministic unit tests.
        reconfigure: Force reconfiguration even if instrumentation appears to
            have been done previously. This is primarily for test scenarios.
    """

    # Bail out if instrumentation already applied (unless caller forces it).
    if getattr(app.state, "otel_configured", False) and not reconfigure:
        return

    # Detach any previous instrumentation to avoid duplicate spans in tests.
    if reconfigure:
        try:
            FastAPIInstrumentor().uninstrument_app(app)
        except Exception:  # pragma: no cover  # noqa: BLE001
            pass

        # Starlette prevents adding middleware after the application has
        # started once (middleware_stack built). Reset the attribute so that
        # re-instrumentation via ``instrument_app`` can run during tests.
        if hasattr(app, "middleware_stack"):
            app.middleware_stack = None  # type: ignore[attr-defined]

    # ---------------------------------------------------------------------
    # Provider & exporter setup
    # ---------------------------------------------------------------------
    service_name = os.getenv("OTEL_SERVICE_NAME", "mcp-observability")

    resource = Resource.create(
        attributes={
            "service.name": service_name,
        }
    )

    if span_exporter is None:
        endpoint = os.getenv(
            "OTEL_EXPORTER_OTLP_ENDPOINT", "http://otel-collector:4318"
        )
        span_exporter = _create_default_exporter(endpoint)

    tracer_provider = TracerProvider(resource=resource)
    processor_cls = SimpleSpanProcessor if use_simple_processor else BatchSpanProcessor
    tracer_provider.add_span_processor(processor_cls(span_exporter))

    # Set global tracer provider *before* instrumentation.
    trace.set_tracer_provider(tracer_provider)

    # ------------------------------------------------------------------
    # Instrumentations
    # ------------------------------------------------------------------
    FastAPIInstrumentor().instrument_app(app, tracer_provider=tracer_provider)
    HTTPXClientInstrumentor().instrument(tracer_provider=tracer_provider)

    # Future: metrics exporter via Prometheus / OTLP

    app.state.otel_configured = True
