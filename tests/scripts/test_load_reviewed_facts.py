from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pytest

from scripts.load_reviewed_facts import run_import


def _record(fact_id: str = "fact-1") -> dict[str, object]:
    return {
        "revisionId": "rev-1",
        "factId": fact_id,
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
    def __init__(self, fail_insert_at: int | None = None) -> None:
        self.fail_insert_at = fail_insert_at
        self.insert_count = 0
        self.inserted: list[tuple[Any, ...]] = []
        self.read_only = False

    @contextmanager
    def transaction(self) -> Iterator[None]:
        before = list(self.inserted)
        try:
            yield
        except Exception:
            self.inserted = before
            raise

    def execute(self, statement: str, params: Any = None) -> _Cursor:
        if statement == "SET TRANSACTION READ ONLY":
            self.read_only = True
            return _Cursor([])
        if "INSERT INTO ai.reviewed_facts" in statement:
            self.insert_count += 1
            if self.insert_count == self.fail_insert_at:
                raise RuntimeError("simulated insert failure")
            self.inserted.append(params)
            return _Cursor([])
        fact_ids = params[1]
        text = "한옥입니다. 주변 산책로가 있습니다."
        return _Cursor([
            {
                "fact_id": fact_id,
                "active_revision": "rev-1",
                "chunk_start_offset": 0,
                "chunk_end_offset": len(text),
                "chunk_text": text,
                "source_id": "p-tourapi-1",
                "eligibility_status": "PUBLIC",
                "normalized_text": text,
                "place_revoked": False,
                "source_revoked": False,
            }
            for fact_id in fact_ids
        ])


def _jsonl(*records: dict[str, object]) -> str:
    return "\n".join(json.dumps(record, ensure_ascii=False) for record in records)


def test_default_import_validates_read_only_without_inserts() -> None:
    connection = _Connection()

    count = run_import(connection, _jsonl(_record()), apply=False)

    assert count == 1
    assert connection.read_only
    assert connection.inserted == []


def test_apply_inserts_validated_fact_rows() -> None:
    connection = _Connection()

    count = run_import(connection, _jsonl(_record()), apply=True)

    assert count == 1
    assert len(connection.inserted) == 1


def test_insert_failure_rolls_back_the_whole_import_transaction() -> None:
    connection = _Connection(fail_insert_at=2)

    with pytest.raises(RuntimeError, match="simulated"):
        run_import(connection, _jsonl(_record(), _record("fact-2")), apply=True)

    assert connection.inserted == []
