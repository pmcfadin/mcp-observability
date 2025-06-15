#!/usr/bin/env python3
"""Simple drift detection between Docker Compose services and Helm chart dependencies.

Exits non-zero if a component appears in one manifest but not the other.
Intended to run in CI.
"""
from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    sys.stderr.write("PyYAML is required for check_drift.py\n")
    sys.exit(2)

COMPOSE_PATH = Path("mcp-obs.yml")
CHART_PATH = Path("charts/mcp-obs/Chart.yaml")

if not COMPOSE_PATH.exists() or not CHART_PATH.exists():
    sys.stderr.write("Compose or Chart file missing.\n")
    sys.exit(2)

compose_services: set[str] = set()
with COMPOSE_PATH.open() as f:
    compose_yaml = yaml.safe_load(f)
    compose_services = set(compose_yaml.get("services", {}).keys())

helm_components: set[str] = set()
with CHART_PATH.open() as f:
    chart_yaml = yaml.safe_load(f)
    deps = chart_yaml.get("dependencies", []) or []
    helm_components = {d.get("name") for d in deps if "name" in d}

# Add umbrella chart local component names
helm_components.add("mcp-server")
# Map naming differences
if "opentelemetry-collector" in helm_components:
    helm_components.remove("opentelemetry-collector")
    helm_components.add("otel-collector")

missing_in_compose = helm_components - compose_services
missing_in_helm = compose_services - helm_components

if missing_in_compose or missing_in_helm:
    print("::error::Drift detected between Compose and Helm manifests")
    if missing_in_compose:
        print(f"Services missing in Compose: {', '.join(sorted(missing_in_compose))}")
    if missing_in_helm:
        print(f"Services missing in Helm: {', '.join(sorted(missing_in_helm))}")
    sys.exit(1)

print("Compose and Helm manifests are in sync ✅") 