from __future__ import annotations

from typing import Any

import pytest

from onmaru_ai.embedding import E5_SMALL_ONNX_INT8_384
from scripts.activate_corpus_revision import activate_candidate_revision


class _Cursor:
    def __init__(self, row: dict[str, Any]) -> None:
        self._row = row

    def fetchone(self) -> dict[str, Any]:
        return self._row


class _Connection:
    def __init__(self, row: dict[str, Any] | None = None) -> None:
        self.row = row or {
            "revision_id": "rev-e5-1",
            "manifest_hash": "sha256:" + "a" * 64,
            "state": "VALIDATED",
            "gc_state": "LIVE",
            "embedding_profile_id": E5_SMALL_ONNX_INT8_384.profile_id,
            "document_count": 3,
            "chunk_count": 3,
            "embedding_count": 3,
            "actual_document_count": 3,
            "actual_chunk_count": 3,
            "actual_embedding_count": 3,
            "active_revision": "rev-old",
            "active_sequence": 12,
            "current_sequence": 12,
            "heartbeat_healthy": True,
        }
        self.queries: list[str] = []

    def execute(self, query: str, _params: tuple[str, ...]) -> _Cursor:
        self.queries.append(query)
        return _Cursor(self.row)


class _Store:
    def __init__(self) -> None:
        self.activations: list[dict[str, Any]] = []

    def activate(self, revision_id: str, **kwargs: Any) -> None:
        self.activations.append({"revision_id": revision_id, **kwargs})


def test_activation_defaults_to_validation_only() -> None:
    connection, store = _Connection(), _Store()

    metadata = activate_candidate_revision(
        connection, store, "rev-e5-1", confirm_revision="rev-e5-1", apply=False
    )

    assert metadata["actual_embedding_count"] == 3
    assert connection.queries
    assert store.activations == []


def test_activation_requires_exact_revision_confirmation() -> None:
    with pytest.raises(ValueError, match="confirmation"):
        activate_candidate_revision(
            _Connection(), _Store(), "rev-e5-1", confirm_revision="rev-other", apply=True
        )


def test_activation_applies_only_after_all_checks_pass() -> None:
    store = _Store()

    activate_candidate_revision(
        _Connection(), store, "rev-e5-1", confirm_revision="rev-e5-1", apply=True
    )

    assert store.activations == [{
        "revision_id": "rev-e5-1",
        "manifest_hash": "sha256:" + "a" * 64,
        "expected_active": "rev-old",
        "expected_revocation_sequence": 12,
    }]


@pytest.mark.parametrize(
    "updates",
    [
        {"embedding_profile_id": "gemini-embedding-001-384@v1"},
        {"state": "ACTIVE"},
        {"actual_embedding_count": 1},
        {"current_sequence": 13},
        {"heartbeat_healthy": False},
    ],
)
def test_activation_rejects_ineligible_revision(
    updates: dict[str, object],
) -> None:
    row = _Connection().row | updates
    store = _Store()

    with pytest.raises(ValueError):
        activate_candidate_revision(
            _Connection(row), store, "rev-e5-1", confirm_revision="rev-e5-1", apply=True
        )

    assert store.activations == []
