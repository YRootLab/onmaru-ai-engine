"""Minimal checksum-locked SQL migration runner for the AI-owned schema."""

from __future__ import annotations

import hashlib
from pathlib import Path

import psycopg
from psycopg import sql


class MigrationError(RuntimeError):
    """A historical migration changed or the migration directory is invalid."""


def apply_migrations(
    connection: psycopg.Connection[tuple[object, ...]], directory: Path
) -> tuple[str, ...]:
    migrations = tuple(sorted(directory.glob("[0-9][0-9][0-9]_*.sql")))
    if not migrations:
        raise MigrationError("NO_MIGRATIONS")
    applied: list[str] = []
    for migration in migrations:
        body = migration.read_text(encoding="utf-8")
        checksum = hashlib.sha256(body.encode()).hexdigest()
        with connection.transaction():
            exists = connection.execute("SELECT to_regclass('ai.schema_migrations')").fetchone()
            if exists is not None and exists[0] is not None:
                row = connection.execute(
                    "SELECT checksum FROM ai.schema_migrations WHERE name=%s",
                    (migration.name,),
                ).fetchone()
                if row is not None:
                    if row[0] != checksum:
                        raise MigrationError("CHECKSUM_MISMATCH")
                    continue
            connection.execute(body)
            connection.execute(
                """CREATE TABLE IF NOT EXISTS ai.schema_migrations (
                       name text PRIMARY KEY,
                       checksum text NOT NULL,
                       applied_at timestamptz NOT NULL DEFAULT now()
                   )"""
            )
            connection.execute(
                "INSERT INTO ai.schema_migrations (name, checksum) VALUES (%s, %s)",
                (migration.name, checksum),
            )
            applied.append(migration.name)
    return tuple(applied)


def grant_roles(
    connection: psycopg.Connection[tuple[object, ...]],
    *,
    runtime_role: str,
    sync_role: str,
) -> None:
    """Grant data access without granting schema object creation."""
    runtime = sql.Identifier(runtime_role)
    sync = sql.Identifier(sync_role)
    with connection.transaction():
        connection.execute(sql.SQL("GRANT USAGE ON SCHEMA ai TO {}").format(runtime))
        connection.execute(sql.SQL("GRANT USAGE ON SCHEMA ai TO {}").format(sync))
        connection.execute(sql.SQL("GRANT SELECT ON ALL TABLES IN SCHEMA ai TO {}").format(runtime))
        connection.execute(
            sql.SQL("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ai TO {}").format(
                sync
            )
        )
