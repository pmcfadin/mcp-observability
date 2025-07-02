#!/usr/bin/env python3
"""doc_inventory.py – quick helper to list markdown documentation files.

Usage:
  python scripts/doc_inventory.py [--json]

By default prints one relative path per line.  If --json is passed prints a
JSON array instead.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import List

ROOT = pathlib.Path(__file__).resolve().parent.parent
DOCS_DIR = ROOT / "docs"


def collect_markdown() -> List[pathlib.Path]:
    """Return a list of all *.md files under docs/ plus the root README."""
    files: List[pathlib.Path] = []
    files.extend(DOCS_DIR.rglob("*.md"))
    readme = ROOT / "README.md"
    if readme.exists():
        files.append(readme)
    # sort paths for deterministic output
    return sorted(files, key=lambda p: str(p))


def main(argv: List[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="List markdown docs")
    parser.add_argument("--json", action="store_true", help="output JSON array")
    args = parser.parse_args(argv)

    paths = [p.relative_to(ROOT) for p in collect_markdown()]

    if args.json:
        json.dump([str(p) for p in paths], sys.stdout, indent=2)
    else:
        for p in paths:
            print(p)


if __name__ == "__main__":
    main()
