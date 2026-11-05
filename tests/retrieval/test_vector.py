from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import pytest

from onmaru_ai.contracts.models import Versions
from onmaru_ai.embedding import E5_SMALL_384, EmbeddingService
from onmaru_ai.retrieval.vector import VectorSearcher, VectorSearchError, VectorSearchFilters
from onmaru_ai.storage.postgres import CorpusSnapshot

PLACE = UUID("00000000-0000-0000-0000-000000000001")
DOCUMENT = UUID("00000000-0000-0000-0000-000000000002")
CHUNK = UUID("00000000-0000-0000-0000-000000000003")


class Backend:
    model_id = E5_SMALL_384.model_id
    model_commit = E5_SMALL_384.model_commit
    dimensions = 384

    def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        return tuple((1.0,) + (0.0,) * 383 for _ in texts)


@dataclass
class Result:
    rows: list[dict[str, Any]]

    def fetchall(self) -> list[dict[str, Any]]:
        return self.rows


class Connection:
    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        self.query = ""
        self.params: tuple[object, ...] = ()

    def execute(self, query: str, params: tuple[object, ...]) -> Result:
        self.query = query
        self.params = params
        return Result(self.rows)


def snapshot(connection: Any, *, profile: str = E5_SMALL_384.profile_id) -> CorpusSnapshot:
    return CorpusSnapshot(
        versions=Versions.model_validate(
            {
                "corpusRevision": "corpus-v1",
                "configHash": "sha256:" + "a" * 64,
                "questionDictionaryVersion": "dictionary-v1",
                "sourceRevocationSequence": 7,
            }
        ),
        embedding_profile_id=profile,
        revoked_places=frozenset(),
        revoked_sources=frozenset(),
        connection=connection,
    )


def row(*, score: float = 0.9) -> dict[str, Any]:
    return {
        "place_id": PLACE,
        "document_id": DOCUMENT,
        "chunk_id": CHUNK,
        "source_type": "TOUR",
        "source_id": "source-1",
        "source_revision": "source-v1",
        "score": score,
    }


def test_search_uses_snapshot_revision_profile_filters_and_deterministic_rank() -> None:
    connection = Connection([row(), {**row(score=0.8), "chunk_id": UUID(int=4)}])
    searcher = VectorSearcher(EmbeddingService(Backend(), profile=E5_SMALL_384))
    filters = VectorSearchFilters(
        place_ids=frozenset({PLACE}), region_codes=frozenset({"KR-11"})
    )

    candidates = searcher.search(snapshot(connection), "한옥", filters=filters, limit=20)

    assert [candidate.rank for candidate in candidates] == [1, 2]
    assert all(candidate.corpus_revision == "corpus-v1" for candidate in candidates)
    assert all(candidate.source_revocation_sequence == 7 for candidate in candidates)
    assert "d.revision_id = %s" in connection.query
    assert "e.embedding_profile_id = %s" in connection.query
    assert "d.eligibility_status = 'PUBLIC'" in connection.query
    assert "place_revocations" in connection.query and "source_revocations" in connection.query
    assert "ORDER BY e.embedding <=> %s::vector, c.chunk_id" in connection.query
    assert isinstance(connection.params[0], list) and len(connection.params[0]) == 384
    assert connection.params[1:3] == ("corpus-v1", E5_SMALL_384.profile_id)
    assert connection.params[-1] == 20


def test_limit_is_fail_closed_above_vector_top_20() -> None:
    searcher = VectorSearcher(EmbeddingService(Backend(), profile=E5_SMALL_384))
    with pytest.raises(VectorSearchError, match="LIMIT_OUT_OF_RANGE"):
        searcher.search(snapshot(Connection([])), "한옥", filters=VectorSearchFilters(), limit=21)


def test_profile_mismatch_fails_before_query() -> None:
    connection = Connection([])
    searcher = VectorSearcher(EmbeddingService(Backend(), profile=E5_SMALL_384))
    with pytest.raises(VectorSearchError, match="PROFILE_MISMATCH"):
        searcher.search(snapshot(connection, profile="other-profile"), "한옥")
    assert connection.query == ""


def test_result_outside_snapshot_or_filters_fails_closed() -> None:
    connection = Connection([{**row(), "place_id": UUID(int=99)}])
    searcher = VectorSearcher(EmbeddingService(Backend(), profile=E5_SMALL_384))
    with pytest.raises(VectorSearchError, match="RESULT_OUTSIDE_FILTERS"):
        searcher.search(
            snapshot(connection),
            "한옥",
            filters=VectorSearchFilters(place_ids=frozenset({PLACE})),
        )


def test_duplicate_or_invalid_score_result_fails_closed() -> None:
    searcher = VectorSearcher(EmbeddingService(Backend(), profile=E5_SMALL_384))
    with pytest.raises(VectorSearchError, match="INVALID_SEARCH_RESULT"):
        searcher.search(snapshot(Connection([row(), row()])), "한옥")
    with pytest.raises(VectorSearchError, match="INVALID_SEARCH_RESULT"):
        searcher.search(snapshot(Connection([row(score=float("nan"))])), "한옥")
