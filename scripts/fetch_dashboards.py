#!/usr/bin/env python3
"""Fetch Grafana dashboards JSON from grafana.com and store them locally.

This helper script downloads public dashboards by ID from the Grafana.com API
and writes the resulting JSON files under ``grafana/dashboards/``.

It is intended to run during CI/build so that the required dashboard assets
are always up-to-date and committed to the repository.

Example:
    poetry run python scripts/fetch_dashboards.py 16110 13175

If no IDs are supplied, the script fetches the two dashboards used by the
Observability stack out of the box (16110 and 13175).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx

API_TEMPLATE = "https://grafana.com/api/dashboards/{id}/revisions/latest/download"
DEFAULT_IDS = [16110, 13175]
DEFAULT_OUTPUT_DIR = Path("grafana/dashboards")


def fetch_dashboard(dashboard_id: int, dest_dir: Path) -> Path:
    """Download a single dashboard JSON and save it under *dest_dir*.

    Returns the path to the written file. Raises ``httpx.HTTPStatusError`` on
    non-200 responses so callers can handle failures explicitly.
    """
    url = API_TEMPLATE.format(id=dashboard_id)
    dest_dir.mkdir(parents=True, exist_ok=True)
    target_path = dest_dir / f"{dashboard_id}.json"

    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
        target_path.write_bytes(response.content)

    return target_path


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:  # noqa: D401
    """Parse command-line options."""
    parser = argparse.ArgumentParser(
        description="Download Grafana dashboard JSON definitions from grafana.com",
    )
    parser.add_argument(
        "ids",
        metavar="ID",
        type=int,
        nargs="*",
        help="Numeric dashboard IDs to download (defaults to 16110 13175)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Destination directory to write JSON files (default: grafana/dashboards)",
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:  # noqa: D401
    """CLI entry-point."""
    args = parse_args(argv)

    ids = args.ids or DEFAULT_IDS
    success: list[int] = []

    for dash_id in ids:
        try:
            path = fetch_dashboard(dash_id, args.output)
            print(f"✅ Downloaded dashboard {dash_id} -> {path}")
            success.append(dash_id)
        except httpx.HTTPStatusError as exc:
            print(
                f"❌ Failed to fetch {dash_id}: HTTP {exc.response.status_code}",
                file=sys.stderr,
            )
            sys.exit(1)
        except Exception as exc:  # noqa: BLE001
            print(f"❌ Failed to fetch {dash_id}: {exc}", file=sys.stderr)
            sys.exit(1)

    if not success:
        print("No dashboards were downloaded", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main() 