from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

MIGRATION = Path(__file__).resolve().parents[3] / "migrations" / "ai" / "001_corpus.sql"


@pytest.fixture
def dsn() -> str:
    import os

    value = os.environ.get("ONMARU_TEST_POSTGRES_DSN")
    if not value:
        pytest.skip(
            "set ONMARU_TEST_POSTGRES_DSN to a disposable PostgreSQL 17 + pgvector database"
        )
    return value


@pytest.fixture
def db(dsn: str) -> Iterator[psycopg.Connection[tuple[object, ...]]]:
    with psycopg.connect(dsn, autocommit=True) as connection:
        connection.execute("DROP SCHEMA IF EXISTS ai CASCADE")
        with connection.transaction():
            connection.execute(MIGRATION.read_text())
        yield connection
        connection.execute("DROP SCHEMA ai CASCADE")
