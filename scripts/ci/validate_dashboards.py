#!/usr/bin/env python3
"""Validate Grafana dashboard JSON files.

Usage: poetry run python scripts/ci/validate_dashboards.py

The script walks through ``grafana/dashboards`` directory and attempts to
load each ``*.json`` file with Python's ``json`` module ensuring they are
valid JSON. It also verifies that each dashboard contains the mandatory
``schemaVersion`` and ``title`` fields.

If any file fails validation, the script prints an error message and exits
with status code 1 (suitable for CI pipelines).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DASHBOARD_DIR = Path("grafana/dashboards")


def validate_file(file_path: Path) -> bool:
    """Return True if dashboard JSON is valid; False otherwise."""
    try:
        data = json.loads(file_path.read_text())
    except json.JSONDecodeError as exc:
        print(f"::error file={file_path}::Invalid JSON – {exc}")
        return False

    required_keys = {"schemaVersion", "title"}
    missing = required_keys - data.keys()
    if missing:
        print(f"::error file={file_path}::Missing keys: {', '.join(missing)}")
        return False
    return True


def main() -> None:  # noqa: D401
    dash_files = list(DASHBOARD_DIR.glob("*.json"))
    if not dash_files:
        print(f"No dashboard JSON files found in {DASHBOARD_DIR}")
        sys.exit(0)

    success = True
    for f in dash_files:
        if not validate_file(f):
            success = False

    if not success:
        sys.exit(1)

    print("All dashboards passed validation ✅")


if __name__ == "__main__":
    main()
