from __future__ import annotations

import json
from typing import Any

import pytest

from onmaru_ai.corpus.reviewed_facts import (
    parse_reviewed_facts_jsonl,
    validate_and_import_reviewed_facts,
)

FACT = {
    "revisionId": "rev-1",
    "factId": "fact-1",
    "chunkId": "6d4209a1-9190-4be9-a4d5-1ba75eb23dbc",
    "placeId": "p-tourapi-1",
    "startOffset": 0,
    "endOffset": 5,
    "factText": "한옥입니다",
    "kind": "FACT",
    "supportType": "HISTORICAL_FACT",
    "timeScope": "TIMELESS",
    "relation": None,
    "reviewStatus": "APPROVED",
    "approvedBy": "reviewer-1",
    "approvedAt": "2026-11-18T04:00:00Z",
}


class _Cursor:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self._rows = rows

    def fetchall(self) -> list[dict[str, Any]]:
        return self._rows


class _Connection:
    def __init__(
        self,
        *,
        source_id: str = "p-tourapi-1",
        active_revision: str = "rev-1",
        **updates: Any,
    ) -> None:
        self.source_id = source_id
        self.active_revision = active_revision
        self.insert_calls: list[tuple[str, tuple[Any, ...]]] = []
        self.query_calls: list[str] = []
        self.place_revoked = False
        self.source_revoked = False
        self.normalized_text = "한옥입니다. 주변 산책로가 있습니다."
        for name, value in updates.items():
            setattr(self, name, value)

    def execute(self, statement: str, params: tuple[Any, ...]) -> _Cursor:
        self.query_calls.append(statement)
        if "INSERT INTO ai.reviewed_facts" in statement:
            self.insert_calls.append((statement, params))
            return _Cursor([])
        assert len(params) == 4
        return _Cursor([{
            "fact_id": "fact-1",
            "active_revision": self.active_revision,
            "chunk_start_offset": 0,
            "chunk_end_offset": len(self.normalized_text),
            "chunk_text": self.normalized_text,
            "source_id": self.source_id,
            "eligibility_status": "PUBLIC",
            "normalized_text": self.normalized_text,
            "place_revoked": self.place_revoked,
            "source_revoked": self.source_revoked,
        }])


def _facts() -> tuple[Any, ...]:
    return parse_reviewed_facts_jsonl(json.dumps(FACT, ensure_ascii=False))


def test_dry_run_validates_without_inserting() -> None:
    connection = _Connection()

    count = validate_and_import_reviewed_facts(connection, _facts(), apply=False)

    assert count == 1
    assert connection.query_calls and "FOR SHARE OF a" not in connection.query_calls[0]
    assert connection.insert_calls == []


@pytest.mark.parametrize(
    "connection_updates",
    [
        {"source_id": "another-place"},
        {"active_revision": "rev-stale"},
        {"place_revoked": True},
        {"source_revoked": True},
        {"normalized_text": "다른 문장입니다."},
    ],
)
def test_invalid_corpus_binding_is_rejected_before_any_insert(
    connection_updates: dict[str, object],
) -> None:
    connection = _Connection()
    for name, value in connection_updates.items():
        setattr(connection, name, value)

    with pytest.raises(ValueError, match="does not match"):
        validate_and_import_reviewed_facts(connection, _facts(), apply=True)

    assert connection.insert_calls == []


def test_apply_inserts_only_after_complete_validation() -> None:
    connection = _Connection()

    count = validate_and_import_reviewed_facts(connection, _facts(), apply=True)

    assert count == 1
    assert len(connection.insert_calls) == 1
    insert_sql, params = connection.insert_calls[0]
    assert "review_status" in insert_sql
    assert params[1] == "fact-1"
    assert params[3] == "p-tourapi-1"
    assert params[10] is None
    assert "FOR SHARE OF a" in connection.query_calls[0]


def test_multiple_revisions_are_rejected_before_database_access() -> None:
    first = FACT
    second = {**FACT, "factId": "fact-2", "revisionId": "rev-2"}
    facts = parse_reviewed_facts_jsonl(
        "\n".join(json.dumps(row) for row in (first, second))
    )
    connection = _Connection()

    with pytest.raises(ValueError, match="one corpus revision"):
        validate_and_import_reviewed_facts(connection, facts, apply=True)

    assert connection.query_calls == []
    assert connection.insert_calls == []
