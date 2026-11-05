from pathlib import Path

import psycopg
import pytest


def test_migration_creates_only_ai_tables(db: psycopg.Connection[tuple[object, ...]]) -> None:
    tables = {r[0] for r in db.execute("SELECT tablename FROM pg_tables WHERE schemaname='ai'")}
    assert {
        "corpus_revisions",
        "active_corpus",
        "documents",
        "chunks",
        "embeddings",
        "rollback_corpus",
        "revocation_state",
        "revocation_events",
        "source_revocations",
        "place_revocations",
        "corpus_sync_runs",
        "gc_runs",
        "gc_checkpoints",
        "gc_audit",
        "revision_holds",
    } <= tables
    assert db.execute("SELECT tablename FROM pg_tables WHERE schemaname='public'").fetchall() == []


@pytest.mark.parametrize(
    "statement",
    [
        "INSERT INTO ai.active_corpus (id, revocation_sequence) VALUES (2, 0)",
        "INSERT INTO ai.revocation_state (id, sequence) VALUES (2, 0)",
        "INSERT INTO ai.revocation_events (sequence, scope, reason_code) "
        "VALUES (1, 'PLACE', 'PRIVATE')",
        "INSERT INTO ai.revocation_events (sequence, scope, reason_code) "
        "VALUES (1, 'SOURCE_REVISION', 'RIGHTS')",
    ],
)
def test_invalid_control_rows_rejected(
    db: psycopg.Connection[tuple[object, ...]],
    statement: str,
) -> None:
    with pytest.raises(psycopg.errors.CheckViolation), db.transaction():
        db.execute(statement)


def test_migration_available() -> None:
    assert (Path(__file__).resolve().parents[2] / "migrations/ai/001_corpus.sql").is_file()


def test_migrations_are_atomic_idempotent_and_checksum_verified(
    db: psycopg.Connection[tuple[object, ...]],
    tmp_path: Path,
) -> None:
    from onmaru_ai.storage.migrations import MigrationError, apply_migrations

    db.execute("DROP SCHEMA ai CASCADE")
    directory = Path(__file__).resolve().parents[2] / "migrations/ai"
    assert apply_migrations(db, directory) == ("001_corpus.sql",)
    assert apply_migrations(db, directory) == ()
    (tmp_path / "001_corpus.sql").write_text("-- changed historical migration")
    with pytest.raises(MigrationError, match="CHECKSUM_MISMATCH"):
        apply_migrations(db, tmp_path)
    (tmp_path / "001_corpus.sql").write_text((directory / "001_corpus.sql").read_text())
    (tmp_path / "002_broken.sql").write_text("CREATE TABLE ai.uncommitted (id int); SELECT 1/0;")
    with pytest.raises(psycopg.errors.DivisionByZero):
        apply_migrations(db, tmp_path)
    assert db.execute("SELECT to_regclass('ai.uncommitted')").fetchone() == (None,)
    assert db.execute("SELECT count(*) FROM ai.schema_migrations").fetchone() == (1,)


def test_runtime_role_cannot_change_active_pointer_or_create_objects(
    db: psycopg.Connection[tuple[object, ...]],
) -> None:
    from onmaru_ai.storage.migrations import grant_roles

    for role in ("w3_test_runtime", "w3_test_sync"):
        if db.execute("SELECT 1 FROM pg_roles WHERE rolname=%s", (role,)).fetchone() is None:
            db.execute(psycopg.sql.SQL("CREATE ROLE {}").format(psycopg.sql.Identifier(role)))
    grant_roles(db, runtime_role="w3_test_runtime", sync_role="w3_test_sync")
    try:
        db.execute("SET ROLE w3_test_runtime")
        assert db.execute("SELECT revision_id FROM ai.active_corpus").fetchone() == (None,)
        for statement in (
            "UPDATE ai.active_corpus SET revocation_sequence=9",
            "CREATE TABLE ai.forbidden (id integer)",
            "DELETE FROM ai.documents",
        ):
            with pytest.raises(psycopg.errors.InsufficientPrivilege), db.transaction():
                db.execute(statement)
        db.execute("RESET ROLE")
        db.execute("SET ROLE w3_test_sync")
        db.execute("UPDATE ai.active_corpus SET revocation_sequence=0")
        with pytest.raises(psycopg.errors.InsufficientPrivilege), db.transaction():
            db.execute("CREATE TABLE ai.forbidden (id integer)")
    finally:
        db.execute("RESET ROLE")
