#!/usr/bin/env python3
"""Validate and optionally import human-approved fact rows into the active corpus."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from onmaru_ai.corpus.reviewed_facts import (
    parse_reviewed_facts_jsonl,
    validate_and_import_reviewed_facts,
)

logger = logging.getLogger("load_reviewed_facts")


def run_import(connection: Any, content: str, *, apply: bool) -> int:
    facts = parse_reviewed_facts_jsonl(content)
    with connection.transaction():
        if not apply:
            connection.execute("SET TRANSACTION READ ONLY")
        return validate_and_import_reviewed_facts(connection, facts, apply=apply)


def main(
    argv: Sequence[str] | None = None,
    *,
    connection_factory: Callable[..., Any] = psycopg.connect,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="UTF-8 JSONL of reviewed fact records")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Insert all validated records in a transaction (default: read-only validation).",
    )
    args = parser.parse_args(argv)
    dsn = os.environ.get("ONMARU_AI_DB_DSN") or os.environ.get("ONMARU_DB_URL")
    if not dsn or not dsn.strip():
        logger.error("Set ONMARU_AI_DB_DSN; no database changes were made")
        return 2

    try:
        content = Path(args.input).read_text(encoding="utf-8")
        with connection_factory(dsn, row_factory=dict_row) as connection:
            count = run_import(connection, content, apply=args.apply)
    except Exception as exc:
        logger.error(
            "Reviewed fact import failed (%s); transaction was rolled back",
            type(exc).__name__,
        )
        return 1

    mode = "inserted" if args.apply else "validated (read-only)"
    logger.info("%s %d reviewed facts", mode, count)
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    sys.exit(main())
