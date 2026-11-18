from __future__ import annotations

import json

import pytest

from onmaru_ai.corpus.reviewed_facts import parse_reviewed_facts_jsonl


def _record(**updates: object) -> dict[str, object]:
    record: dict[str, object] = {
        "revisionId": "rev-1",
        "factId": "fact-1",
        "chunkId": "6d4209a1-9190-4be9-a4d5-1ba75eb23dbc",
        "placeId": "p-tourapi-1",
        "startOffset": 0,
        "endOffset": 6,
        "factText": "한옥입니다",
        "kind": "FACT",
        "supportType": "HISTORICAL_FACT",
        "timeScope": "TIMELESS",
        "relation": None,
        "reviewStatus": "APPROVED",
        "approvedBy": "reviewer-1",
        "approvedAt": "2026-11-18T04:00:00Z",
    }
    record.update(updates)
    return record


def test_parser_accepts_explicitly_approved_jsonl_fact() -> None:
    parsed = parse_reviewed_facts_jsonl(json.dumps(_record(), ensure_ascii=False))

    assert len(parsed) == 1
    assert parsed[0].fact_id == "fact-1"
    assert parsed[0].place_id == "p-tourapi-1"


@pytest.mark.parametrize(
    "updates",
    [
        {"reviewStatus": "DRAFT", "approvedBy": None, "approvedAt": None},
        {"approvedBy": "", "approvedAt": "2026-11-18T04:00:00Z"},
        {"endOffset": 0},
        {"unknownField": "reject"},
        {"factText": "https://example.com"},
        {"factText": "첫 문장입니다. 두 번째 문장입니다."},
        {"timeScope": "http://example.com"},
    ],
)
def test_parser_rejects_unapproved_or_invalid_fact(updates: dict[str, object]) -> None:
    with pytest.raises(ValueError, match="line 1"):
        parse_reviewed_facts_jsonl(json.dumps(_record(**updates), ensure_ascii=False))


def test_parser_rejects_duplicate_revision_fact_ids() -> None:
    line = json.dumps(_record(), ensure_ascii=False)
    with pytest.raises(ValueError, match="duplicate"):
        parse_reviewed_facts_jsonl(f"{line}\n{line}")
