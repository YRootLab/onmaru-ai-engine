"""W1 acceptance cases exercise immutable fixtures and preparation outputs."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest

if TYPE_CHECKING:
    from onmaru_ai.corpus.source_sync import SourceManifestReceiver

FIXTURE = Path(__file__).parent / "fixtures" / "public-manifest.json"


def manifest() -> dict[str, Any]:
    return json.loads(FIXTURE.read_text())  # type: ignore[no-any-return]


def signed(payload: dict[str, Any]) -> dict[str, Any]:
    """Independent Spring-side canonicalization, never the receiver's hash helper."""
    unsigned = {key: value for key, value in payload.items() if key != "manifestHash"}
    payload["manifestHash"] = (
        "sha256:"
        + hashlib.sha256(
            json.dumps(unsigned, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
    )
    return payload


def receiver() -> SourceManifestReceiver:
    from onmaru_ai.corpus.source_sync import SourceManifestReceiver

    return SourceManifestReceiver()


def next_manifest() -> dict[str, Any]:
    payload = manifest()
    payload.update(
        revisionId="catalog-r2",
        sourceRevision="spring-export-2",
        publishedAt="2026-11-05T01:00:00Z",
    )
    return payload


def tombstone(sequence: int = 1, *, scope: str = "SOURCE_REVISION") -> dict[str, Any]:
    return {
        "sequence": sequence,
        "scope": scope,
        "sourceType": "TOUR_API" if scope == "SOURCE_REVISION" else None,
        "sourceId": "tour-1" if scope == "SOURCE_REVISION" else None,
        "sourceRevision": "tour-r1" if scope == "SOURCE_REVISION" else None,
        "placeId": "place-1" if scope == "PLACE" else None,
        "revokedAt": "2026-11-05T00:30:00Z",
        "reasonCode": "RIGHTS_REVOKED",
    }


def test_fixed_manifest_is_prepared_once() -> None:
    sync = receiver()
    first = sync.receive(manifest())
    replay = sync.receive(manifest())
    assert first.status == "PREPARED"
    assert [doc.document_id for doc in first.prepared_documents] == ["doc-1"]
    assert first.manifest_hash == manifest()["manifestHash"]
    assert first.source_revision == "spring-export-1"
    assert replay.status == "DUPLICATE"
    assert replay.prepared_documents == ()
    assert sync.latest_revision_id == "catalog-r1"
    assert sync.watermark == 0


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("licenseVerified", False),
        ("licenseCode", None),
        ("licenseCode", ""),
        ("publicationEligible", False),
        ("public", False),
        ("revoked", True),
        ("snapshotStatus", "FAILED"),
        ("sourceType", "MEMBER_DATA"),
    ],
)
def test_ineligible_source_never_reaches_preparation(field: str, value: object) -> None:
    payload = manifest()
    payload["documents"][0][field] = value
    result = receiver().receive(signed(payload))
    assert result.status == "PREPARED"
    assert result.prepared_documents == ()
    assert result.excluded_document_ids == ("doc-1",)


@pytest.mark.parametrize(
    ("source_type", "review", "expected_count"),
    [
        ("K_CONTENTS", "VERIFIED", 1),
        ("K_CONTENTS", "REVIEW_REQUIRED", 0),
        ("K_CONTENTS", None, 0),
        ("PLACE_CANONICAL", None, 1),
    ],
)
def test_source_specific_verification(
    source_type: str, review: str | None, expected_count: int
) -> None:
    payload = manifest()
    payload["documents"][0].update(sourceType=source_type, reviewStatus=review)
    result = receiver().receive(signed(payload))
    assert result.status == "PREPARED"
    assert len(result.prepared_documents) == expected_count


@pytest.mark.parametrize("scope", ["SOURCE_REVISION", "PLACE"])
def test_tombstones_filter_current_and_later_preparation(scope: str) -> None:
    sync = receiver()
    payload = manifest()
    payload.update(revocationSequence=1, tombstones=[tombstone(scope=scope)])
    first = sync.receive(signed(payload))
    later = sync.receive(signed({**next_manifest(), "revocationSequence": 1}))
    assert first.prepared_documents == ()
    assert later.prepared_documents == ()
    assert sync.watermark == 1


def test_reapproved_source_revision_does_not_unrevoke_old_revision() -> None:
    sync = receiver()
    payload = manifest()
    payload.update(revocationSequence=1, tombstones=[tombstone()])
    sync.receive(signed(payload))
    newer = next_manifest()
    newer["revocationSequence"] = 1
    newer["documents"][0]["sourceRevision"] = "tour-r2"
    assert len(sync.receive(signed(newer)).prepared_documents) == 1
    old = next_manifest()
    old.update(revisionId="catalog-r3", publishedAt="2026-11-05T02:00:00Z", revocationSequence=1)
    assert sync.receive(signed(old)).prepared_documents == ()


@pytest.mark.parametrize("sequences", [[2], [1, 3], [], [2, 1], [1, 1]])
def test_missing_duplicate_or_reversed_sequence_never_advances_state(
    sequences: list[int],
) -> None:
    sync = receiver()
    payload = manifest()
    payload.update(revocationSequence=2, tombstones=[tombstone(seq) for seq in sequences])
    result = sync.receive(signed(payload))
    assert result.status == "REJECTED"
    assert result.prepared_documents == ()
    assert sync.watermark == 0
    assert sync.latest_revision_id is None
    # A repaired manifest with the same revision is still ingestible.
    payload.update(revocationSequence=1, tombstones=[tombstone()])
    assert sync.receive(signed(payload)).status == "PREPARED"
    assert sync.watermark == 1


def test_exact_tombstone_replay_is_idempotent_but_changed_event_is_rejected() -> None:
    sync = receiver()
    payload = manifest()
    payload.update(revocationSequence=1, tombstones=[tombstone()])
    assert sync.receive(signed(payload)).status == "PREPARED"
    newer = next_manifest()
    newer.update(revocationSequence=1, tombstones=[tombstone()])
    assert sync.receive(signed(newer)).status == "PREPARED"
    conflicting = copy.deepcopy(newer)
    conflicting.update(revisionId="catalog-r3", publishedAt="2026-11-05T02:00:00Z")
    conflicting["tombstones"][0]["sourceRevision"] = "tour-r2"
    result = sync.receive(signed(conflicting))
    assert result.status == "REJECTED"
    assert result.error_code == "TOMBSTONE_SEQUENCE_CONFLICT"
    assert sync.watermark == 1
    assert sync.latest_revision_id == "catalog-r2"


@pytest.mark.parametrize(
    "mutation",
    ["hash", "count", "duplicate", "schema", "boolean", "missing-revision", "naive-time", "scope"],
)
def test_invalid_manifest_is_rejected_atomically(mutation: str) -> None:
    sync = receiver()
    payload = manifest()
    if mutation == "hash":
        payload["documents"][0]["public"] = False
    elif mutation == "count":
        payload["documentCount"] = 2
    elif mutation == "duplicate":
        payload["documents"].append(copy.deepcopy(payload["documents"][0]))
        payload["documentCount"] = 2
    elif mutation == "schema":
        payload["contractVersion"] = "2.0"
    elif mutation == "boolean":
        payload["documents"][0]["public"] = "true"
    elif mutation == "missing-revision":
        del payload["documents"][0]["sourceRevision"]
    elif mutation == "naive-time":
        payload["publishedAt"] = "2026-11-05T00:00:00"
    else:
        payload.update(revocationSequence=1, tombstones=[tombstone()])
        payload["tombstones"][0]["sourceId"] = None
    result = sync.receive(payload if mutation == "hash" else signed(payload))
    assert result.status == "REJECTED"
    assert result.prepared_documents == ()
    assert sync.latest_revision_id is None
    assert sync.watermark == 0


def test_revision_conflicts_and_reversal_do_not_replace_latest_manifest() -> None:
    sync = receiver()
    assert sync.receive(manifest()).status == "PREPARED"
    changed = manifest()
    changed["documents"][0]["documentHash"] = "sha256:" + "b" * 64
    assert sync.receive(signed(changed)).error_code == "MANIFEST_REVISION_CONFLICT"
    assert sync.receive(signed(next_manifest())).status == "PREPARED"
    stale = next_manifest()
    stale.update(revisionId="catalog-r0", publishedAt="2026-11-04T00:00:00Z")
    assert sync.receive(signed(stale)).error_code == "MANIFEST_OUT_OF_ORDER"
    assert sync.receive(manifest()).status == "DUPLICATE"
    assert sync.latest_revision_id == "catalog-r2"


def test_immutable_source_revision_cannot_change_content() -> None:
    sync = receiver()
    sync.receive(manifest())
    newer = next_manifest()
    newer["documents"][0]["documentHash"] = "sha256:" + "b" * 64
    result = sync.receive(signed(newer))
    assert result.status == "REJECTED"
    assert result.error_code == "SOURCE_REVISION_CONFLICT"
    assert sync.latest_revision_id == "catalog-r1"


def test_watermark_reversal_is_rejected_after_a_valid_sequence() -> None:
    sync = receiver()
    payload = manifest()
    payload.update(revocationSequence=1, tombstones=[tombstone()])
    sync.receive(signed(payload))
    assert sync.receive(signed(next_manifest())).error_code == "TOMBSTONE_SEQUENCE_REVERSED"
    assert sync.watermark == 1
