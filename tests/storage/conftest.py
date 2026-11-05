from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest

MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations" / "ai"


@pytest.fixture
def dsn(monkeypatch: pytest.MonkeyPatch) -> str:
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
        # Explicit test DSN only: this fixture destroys the AI schema between tests.
        connection.execute("DROP SCHEMA IF EXISTS ai CASCADE")
        migration = MIGRATIONS / "001_corpus.sql"
        assert migration.exists(), "AI schema migration is missing"
        with connection.transaction():
            connection.execute(migration.read_text())
        yield connection
        connection.execute("DROP SCHEMA ai CASCADE")
