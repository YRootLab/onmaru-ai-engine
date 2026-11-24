from unittest.mock import MagicMock

import pytest

from onmaru_ai.storage.readiness import corpus_ready


@pytest.mark.parametrize("row", [None, (False,), (True,)])
def test_corpus_readiness_fails_closed_unless_all_db_gates_pass(row: object) -> None:
    connection = MagicMock()
    connection.execute.return_value.fetchone.return_value = row
    assert corpus_ready(connection) is (row == (True,))


def test_empty_migrated_database_is_not_ready(db: object) -> None:
    from pathlib import Path
    from typing import cast

    import psycopg

    connection = cast(psycopg.Connection[tuple[object, ...]], db)
    migrations = Path(__file__).resolve().parents[2] / 'migrations' / 'ai'
    connection.execute((migrations / '003_reviewed_facts.sql').read_text())
    connection.execute((migrations / '004_pg_search_bm25.sql').read_text())
    connection.execute((migrations / '005_source_revocation_bootstrap.sql').read_text())
    assert not corpus_ready(connection)
