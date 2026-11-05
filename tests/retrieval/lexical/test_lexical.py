from __future__ import annotations

from collections.abc import Iterator
from dataclasses import replace
from typing import Any
from uuid import UUID

import pytest

from onmaru_ai.contracts.models import HardFilters, Versions
from onmaru_ai.corpus.bm25 import KoreanBm25, KoreanTokenizer
from onmaru_ai.retrieval.lexical import (
    LexicalChunk,
    LexicalIndexError,
    LexicalRequest,
    LexicalSearchAdapter,
    PostgresLexicalChunkRepository,
)
from onmaru_ai.storage.postgres import CorpusSnapshot

RUN_ID = "123e4567-e89b-12d3-a456-426614174000"
PLAN_HASH = "sha256:" + "a" * 64
CONFIG_HASH = "sha256:" + "b" * 64
PLACE = UUID("123e4567-e89b-12d3-a456-426614174001")


class Repository:
    def __init__(
        self,
        chunks: tuple[LexicalChunk, ...],
        *,
        index_version: str = "ko-bm25-v1",
        available: bool = True,
    ) -> None:
        self.chunks = chunks
        self.index_version = index_version
        self.available = available

    def load(self, snapshot: CorpusSnapshot, request: LexicalRequest) -> tuple[LexicalChunk, ...]:
        if not self.available:
            raise LexicalIndexError("BM25_EXTENSION_UNAVAILABLE")
        if request.index_version != self.index_version:
            raise LexicalIndexError("BM25_INDEX_VERSION_MISMATCH")
        return self.chunks


def versions(**changes: object) -> Versions:
    values: dict[str, object] = {
        "corpusRevision": "corpus-r1",
        "configHash": CONFIG_HASH,
        "questionDictionaryVersion": "dictionary-v1",
        "sourceRevocationSequence": 3,
    }
    values.update(changes)
    return Versions.model_validate(values)


def request(**changes: object) -> LexicalRequest:
    values: dict[str, object] = {
        "runId": RUN_ID,
        "planHash": PLAN_HASH,
        "versions": versions(),
        "query": "북촌한옥마을은 어디인가요",
        "filters": HardFilters.model_validate(
            {
                "filterHash": "sha256:" + "c" * 64,
                "publicOnly": True,
                "placeIds": None,
                "regionCodes": ("11",),
                "categoryCodes": ("HANOK",),
                "pinnedPlaceIds": (),
                "excludedPlaceIds": (),
            }
        ),
        "indexVersion": "ko-bm25-v1",
    }
    values.update(changes)
    return LexicalRequest.model_validate(values)


def chunk(number: int, **changes: object) -> LexicalChunk:
    values: dict[str, Any] = {
        "chunk_id": f"chunk-{number:02d}",
        "place_id": str(PLACE),
        "source_id": f"source-{number:02d}",
        "source_revision": "source-r1",
        "corpus_revision": "corpus-r1",
        "region_code": "11",
        "category_code": "HANOK",
        "text": "북촌 한옥 마을은 서울의 전통 주거 지역이다",
        "exact_names": ("북촌 한옥마을", "북촌한옥마을"),
        "public": True,
    }
    values.update(changes)
    return LexicalChunk(**values)


def snapshot(**changes: object) -> CorpusSnapshot:
    values: dict[str, object] = {
        "versions": versions(),
        "embedding_profile_id": "e5-small-384",
        "revoked_places": frozenset(),
        "revoked_sources": frozenset(),
        "connection": object(),
    }
    values.update(changes)
    return CorpusSnapshot(**values)  # type: ignore[arg-type]


def test_korean_tokenizer_strips_common_particles_without_splitting_names() -> None:
    tokenizer = KoreanTokenizer()

    assert tokenizer.tokenize("북촌한옥마을은 경복궁과 가깝습니다") == (
        "북촌한옥마을",
        "경복궁",
        "가깝습니다",
    )


def test_exact_alias_beats_higher_body_frequency_and_preserves_target_id() -> None:
    exact = chunk(1, text="서울 전통 마을", exact_names=("북촌한옥마을",))
    repeated = chunk(
        2,
        place_id="123e4567-e89b-12d3-a456-426614174002",
        text="북촌한옥마을 북촌한옥마을 북촌한옥마을",
        exact_names=("다른 장소",),
    )

    result = LexicalSearchAdapter(Repository((repeated, exact))).search(request(), snapshot())

    assert [item.chunk_id for item in result.candidates] == ["chunk-01", "chunk-02"]
    assert result.candidates[0].place_id == str(PLACE)
    assert result.stage == "LEXICAL"
    assert result.retrieval_status == "COMPLETE"


def test_prefix_alias_matches_normalized_korean_query() -> None:
    target = chunk(1, exact_names=("전주한옥마을 경기전길",), text="전통 거리")

    result = LexicalSearchAdapter(Repository((target,))).search(
        request(query="전주한옥마을의 경기전길"), snapshot()
    )

    assert [item.chunk_id for item in result.candidates] == ["chunk-01"]


def test_hard_filters_revocations_and_public_scope_apply_before_top_twenty() -> None:
    eligible = tuple(chunk(index) for index in range(30))
    rejected = (
        chunk(31, public=False),
        chunk(32, region_code="26"),
        chunk(33, category_code="FOOD"),
        chunk(34, place_id="123e4567-e89b-12d3-a456-426614174099"),
        chunk(35, source_id="revoked-source"),
        chunk(36, corpus_revision="corpus-r0"),
    )
    filtered_snapshot = snapshot(
        revoked_places=frozenset({UUID("123e4567-e89b-12d3-a456-426614174099")}),
        revoked_sources=frozenset({("TOUR_API", "revoked-source", "source-r1")}),
    )

    result = LexicalSearchAdapter(Repository(eligible + rejected)).search(
        request(), filtered_snapshot
    )

    assert len(result.candidates) == 20
    assert [item.rank for item in result.candidates] == list(range(1, 21))
    assert [item.chunk_id for item in result.candidates] == [
        f"chunk-{index:02d}" for index in range(20)
    ]
    assert all(item.exclusion_reason is None for item in result.candidates)


def test_ties_are_deterministic_by_chunk_id() -> None:
    documents = tuple(
        replace(chunk(index), chunk_id=value)
        for index, value in enumerate(("z", "a", "m"))
    )
    adapter = LexicalSearchAdapter(Repository(documents), clock_ns=lambda: 0)

    first = adapter.search(request(), snapshot())
    second = adapter.search(request(), snapshot())

    assert [item.chunk_id for item in first.candidates] == ["a", "m", "z"]
    assert first == second


def test_no_matching_tokens_returns_closed_no_evidence_candidate_set() -> None:
    result = LexicalSearchAdapter(Repository((chunk(1, text="완전히 다른 본문"),))).search(
        request(query="검색불가질의"), snapshot()
    )

    assert result.candidates == ()
    assert result.retrieval_status == "NO_EVIDENCE"


@pytest.mark.parametrize(
    ("repo", "expected"),
    [
        (Repository((), available=False), "BM25_EXTENSION_UNAVAILABLE"),
        (Repository((), index_version="ko-bm25-v2"), "BM25_INDEX_VERSION_MISMATCH"),
    ],
)
def test_missing_extension_or_wrong_index_version_fails_explicitly(
    repo: Repository, expected: str
) -> None:
    with pytest.raises(LexicalIndexError, match=expected):
        LexicalSearchAdapter(repo).search(request(), snapshot())


def test_snapshot_version_mismatch_fails_before_search() -> None:
    with pytest.raises(LexicalIndexError, match="CORPUS_SNAPSHOT_VERSION_MISMATCH"):
        LexicalSearchAdapter(Repository((chunk(1),))).search(
            request(), snapshot(versions=versions(corpusRevision="corpus-r2"))
        )


def test_bm25_rewards_rare_matching_term() -> None:
    scorer = KoreanBm25()
    scores = scorer.score(
        ("희귀어",),
        (("희귀어", "공통"), ("공통", "공통"), ("공통",)),
    )

    assert scores[0] > 0
    assert scores[1:] == (0.0, 0.0)


class _Rows:
    def __init__(self, rows: tuple[dict[str, object], ...]) -> None:
        self._rows = rows

    def fetchone(self) -> dict[str, object] | None:
        return self._rows[0] if self._rows else None

    def __iter__(self) -> Iterator[dict[str, object]]:
        return iter(self._rows)


class _Connection:
    def __init__(self, extension: bool) -> None:
        self.extension = extension

    def execute(self, statement: str, parameters: object = None) -> _Rows:
        if "pg_extension" in statement:
            return _Rows(({"extversion": "0.20.3"},) if self.extension else ())
        assert "d.eligibility_status='PUBLIC'" in statement
        assert parameters == ("corpus-r1",)
        return _Rows(
            (
                {
                    "chunk_id": "chunk-1",
                    "place_id": PLACE,
                    "source_type": "TOUR_API",
                    "source_id": "source-1",
                    "source_revision": "source-r1",
                    "corpus_revision": "corpus-r1",
                    "region_code": "11",
                    "category_code": "HANOK",
                    "text": "북촌한옥마을",
                    "title": "북촌 한옥마을",
                    "eligibility_status": "PUBLIC",
                },
            )
        )


def test_postgres_repository_requires_real_bm25_extension() -> None:
    repository = PostgresLexicalChunkRepository()
    unavailable = snapshot(connection=_Connection(False))

    with pytest.raises(LexicalIndexError, match="BM25_EXTENSION_UNAVAILABLE"):
        repository.load(unavailable, request())

    loaded = repository.load(snapshot(connection=_Connection(True)), request())
    assert loaded[0].exact_names == ("북촌 한옥마을",)
    assert loaded[0].public is True


def test_postgres_repository_rejects_configured_index_version_mismatch() -> None:
    repository = PostgresLexicalChunkRepository(index_version="ko-bm25-v2")

    with pytest.raises(LexicalIndexError, match="BM25_INDEX_VERSION_MISMATCH"):
        repository.load(snapshot(connection=_Connection(True)), request())
