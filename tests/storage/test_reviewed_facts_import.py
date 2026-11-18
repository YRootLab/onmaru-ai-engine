from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
import pytest
from psycopg.rows import dict_row

from onmaru_ai.corpus.reviewed_facts import (
    parse_reviewed_facts_jsonl,
    validate_and_import_reviewed_facts,
)

MIGRATIONS = Path(__file__).resolve().parents[2] / "migrations" / "ai"
REVISION_ID = "rev-reviewed-facts-test"
DOCUMENT_ID = UUID("dfac0892-88c9-4b16-8b93-7b27543a5d48")
CHUNK_ID = UUID("6d4209a1-9190-4be9-a4d5-1ba75eb23dbc")
PLACE_UUID = UUID("abb3f8d7-48a8-4c80-aa46-b6ff4d5eb729")
TEXT = "한옥입니다. 주변 산책로가 있습니다."


def _seed_active_corpus(connection: psycopg.Connection[Any]) -> None:
    connection.execute(
        """INSERT INTO ai.corpus_revisions (
               revision_id, manifest_hash, manifest, source_revision, state,
               embedding_profile_id, chunker_version, dictionary_version, config_hash,
               document_count, chunk_count, embedding_count
           ) VALUES (%s, %s, %s, %s, 'ACTIVE', %s, %s, %s, %s, 1, 1, 1)""",
        (
            REVISION_ID,
            "manifest-reviewed-facts-test",
            json.dumps({}),
            "source-r1",
            "gemini-embedding-001-384@v1",
            "chunker-test",
            "dictionary-test",
            "config-test",
        ),
    )
    connection.execute(
        """INSERT INTO ai.documents (
               revision_id, document_id, place_id, source_type, source_id, source_revision,
               title, published_at, collected_at, license_code, region_code, category_code,
               content_hash, normalized_text, eligibility_status
           ) VALUES (%s,%s,%s,'TOUR_API','p-tourapi-1','source-r1',%s,now(),now(),
                     'KOGL-1','KR-11','HANOK','sha256:test',%s,'PUBLIC')""",
        (REVISION_ID, DOCUMENT_ID, PLACE_UUID, "한옥 명소", TEXT),
    )
    connection.execute(
        """INSERT INTO ai.chunks (
               revision_id, chunk_id, document_id, ordinal, start_offset, end_offset,
               chunk_text, content_hash, search_text
           ) VALUES (%s,%s,%s,0,0,%s,%s,'sha256:chunk','한옥 명소 한옥')""",
        (REVISION_ID, CHUNK_ID, DOCUMENT_ID, len(TEXT), TEXT),
    )
    connection.execute(
        "UPDATE ai.active_corpus SET revision_id=%s, revocation_sequence=0 WHERE id=1",
        (REVISION_ID,),
    )


def test_reviewed_facts_migration_and_import_round_trip(
    db: psycopg.Connection[Any],
) -> None:
    db.row_factory = dict_row
    db.execute((MIGRATIONS / "003_reviewed_facts.sql").read_text(encoding="utf-8"))
    _seed_active_corpus(db)
    record = {
        "revisionId": REVISION_ID,
        "factId": "fact-reviewed-1",
        "chunkId": str(CHUNK_ID),
        "placeId": "p-tourapi-1",
        "startOffset": 0,
        "endOffset": 5,
        "factText": "한옥입니다",
        "kind": "FACT",
        "supportType": "HISTORICAL_FACT",
        "timeScope": "TIMELESS",
        "relation": None,
        "reviewStatus": "APPROVED",
        "approvedBy": "content-reviewer-1",
        "approvedAt": "2026-11-18T04:00:00Z",
    }
    facts = parse_reviewed_facts_jsonl(json.dumps(record, ensure_ascii=False))

    with db.transaction():
        db.execute("SET TRANSACTION READ ONLY")
        assert validate_and_import_reviewed_facts(db, facts, apply=False) == 1
    count_row = db.execute("SELECT count(*) AS n FROM ai.reviewed_facts").fetchone()
    assert count_row is not None and count_row["n"] == 0

    with db.transaction():
        assert validate_and_import_reviewed_facts(db, facts, apply=True) == 1
    row = db.execute(
        "SELECT review_status, approved_by, fact_text, relation FROM ai.reviewed_facts"
    ).fetchone()
    assert row == {
        "review_status": "APPROVED",
        "approved_by": "content-reviewer-1",
        "fact_text": "한옥입니다",
        "relation": None,
    }

    new_record = {**record, "factId": "fact-reviewed-2"}
    rollback_batch = (
        *parse_reviewed_facts_jsonl(json.dumps(new_record, ensure_ascii=False)),
        *facts,
    )
    with pytest.raises(psycopg.errors.UniqueViolation), db.transaction():
        validate_and_import_reviewed_facts(db, rollback_batch, apply=True)
    ids_row = db.execute(
        "SELECT array_agg(fact_id ORDER BY fact_id) AS ids FROM ai.reviewed_facts"
    ).fetchone()
    assert ids_row is not None and ids_row["ids"] == ["fact-reviewed-1"]
