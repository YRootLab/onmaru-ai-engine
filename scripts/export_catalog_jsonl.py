#!/usr/bin/env python3
"""Export a bounded catalog snapshot as JSONL for offline local embedding."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path

try:
    from scripts.ingest_catalog_from_postgres import iter_catalog_items
except ModuleNotFoundError:
    from ingest_catalog_from_postgres import iter_catalog_items


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    dsn = os.environ.get("ONMARU_AI_CATALOG_READ_DSN", "").strip()
    if not dsn:
        print("Set ONMARU_AI_CATALOG_READ_DSN", file=sys.stderr)
        return 2
    if args.limit < 1:
        parser.error("--limit must be positive")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    count = 0
    try:
        with temporary.open("w", encoding="utf-8") as output:
            for item in iter_catalog_items(dsn, limit=args.limit):
                output.write(json.dumps(asdict(item), ensure_ascii=False) + "\n")
                count += 1
        temporary.replace(args.output)
    except Exception as error:
        temporary.unlink(missing_ok=True)
        print(f"Catalog export failed ({type(error).__name__})", file=sys.stderr)
        return 1
    print(f"Exported {count} catalog places to {args.output}")
    if count != args.limit:
        print(f"Requested {args.limit} rows but source returned {count}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
