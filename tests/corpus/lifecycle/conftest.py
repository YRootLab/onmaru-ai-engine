from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

MIGRATION_DIR = Path(__file__).resolve().parents[3] / "migrations" / "ai"
MIGRATIONS = (
    MIGRATION_DIR / "001_corpus.sql",
    MIGRATION_DIR / "005_source_revocation_bootstrap.sql",
)


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
        for migration in MIGRATIONS:
            with connection.transaction():
                connection.execute(migration.read_text())
        yield connection
        connection.execute("DROP SCHEMA ai CASCADE")
