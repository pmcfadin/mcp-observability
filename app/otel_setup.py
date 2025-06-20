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
from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# Instrumentations
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

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


def configure_opentelemetry(app: FastAPI) -> None:
    """Configure OpenTelemetry for the FastAPI application."""

    service_name = os.getenv("OTEL_SERVICE_NAME", "mcp-observability")

    resource = Resource.create(
        attributes={
            "service.name": service_name,
        }
    )

    # Set up trace provider
    tracer_provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(tracer_provider)

    # Use OTLP exporter over HTTP
    # Assumes collector is running at http://otel-collector:4318/v1/traces
    span_exporter = OTLPSpanExporter()
    tracer_provider.add_span_processor(BatchSpanProcessor(span_exporter))

    # Set up meter provider
    metric_reader = PeriodicExportingMetricReader(OTLPMetricExporter())
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app, tracer_provider=tracer_provider, meter_provider=meter_provider
    )
