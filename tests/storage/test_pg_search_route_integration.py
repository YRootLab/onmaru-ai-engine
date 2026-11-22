"""Disposable PostgreSQL + pg_search coverage for real retrieval SQL routes.

Set ONMARU_TEST_POSTGRES_DSN only to an isolated database: the shared storage fixture
drops and recreates its ``ai`` schema. Synthetic rows exercise SQL behavior, not search quality.
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import psycopg
import pytest

from onmaru_ai.contracts.models import ApprovedQueryPlan, HardFilters
from onmaru_ai.embedding import EmbeddingProfile, EmbeddingService
from onmaru_ai.retrieval.hybrid import HybridRetrievalCoordinator, HybridSearchRequest
from onmaru_ai.retrieval.lexical import (
    LexicalRequest,
    LexicalSearchAdapter,
    PostgresLexicalChunkRepository,
)
from onmaru_ai.retrieval.vector import VectorSearcher, VectorSearchError, VectorSearchFilters
from onmaru_ai.storage.models import Chunk, Document, Embedding, Revision, text_hash
from onmaru_ai.storage.postgres import CorpusSnapshot, PostgresCorpusStore

ROOT = Path(__file__).resolve().parents[2]
PROFILE = EmbeddingProfile(
    profile_id="integration-e5-384",
    model_id="integration-e5",
    model_commit="fixture-v1",
    dimensions=384,
    passage_prefix="passage: ",
    query_prefix="query: ",
)
RUN_ID = "123e4567-e89b-12d3-a456-426614174000"
PLAN_HASH = "sha256:" + "a" * 64


class FixedBackend:
    model_id = PROFILE.model_id
    model_commit = PROFILE.model_commit
    dimensions = PROFILE.dimensions

    def __init__(self, *, output_dimensions: int = 384) -> None:
        self.output_dimensions = output_dimensions

    def encode(self, texts: tuple[str, ...]) -> Sequence[Sequence[float]]:
        return tuple(
            tuple([1.0] + [0.0] * (self.output_dimensions - 1)) for _ in range(len(texts))
        )


@dataclass(frozen=True)
class SearchCase:
    store: PostgresCorpusStore


def _bundle() -> tuple[
    Revision, tuple[Document, ...], tuple[Chunk, ...], tuple[Embedding, ...]
]:
    now = datetime(2026, 11, 20, tzinfo=UTC)
    specs = (
        (
            "p-tourapi-bukchon",
            "북촌 한옥마을",
            "KR-11",
            "HANOK",
            "북촌 한옥마을은 서울 도심의 한옥과 전통 주거 문화를 볼 수 있습니다.",
            1,
        ),
        (
            "p-tourapi-jeonju",
            "전주 한옥마을",
            "KR-45",
            "HANOK",
            "전주 한옥마을에서 전통 한옥과 문화를 즐길 수 있습니다.",
            2,
        ),
        (
            "p-tourapi-museum",
            "국립현대미술관 서울관",
            "KR-11",
            "CULTURE_ART",
            "서울관은 현대 미술 전시를 관람하는 미술관입니다.",
            3,
        ),
    )
    documents: list[Document] = []
    chunks: list[Chunk] = []
    embeddings: list[Embedding] = []
    for source_id, title, region, category, body, number in specs:
        document_id = UUID(f"00000000-0000-0000-0000-{number:012d}")
        place_id = UUID(f"10000000-0000-0000-0000-{number:012d}")
        chunk_id = UUID(f"20000000-0000-0000-0000-{number:012d}")
        documents.append(
            Document(
                document_id=document_id,
                place_id=place_id,
                source_type="TOUR_API",
                source_id=source_id,
                source_revision="fixture-r1",
                title=title,
                published_at=now,
                collected_at=now,
                license_code="KOGL-1",
                region_code=region,
                category_code=category,
                normalized_text=body,
                content_hash=text_hash(body),
            )
        )
        chunks.append(
            Chunk(
                chunk_id=chunk_id,
                document_id=document_id,
                ordinal=0,
                start_offset=0,
                end_offset=len(body),
                chunk_text=body,
                content_hash=text_hash(body),
                search_text=f"{title} {body}",
            )
        )
        vector = tuple(1.0 if position == number - 1 else 0.0 for position in range(384))
        embeddings.append(Embedding(chunk_id, PROFILE.profile_id, vector))
    document_tuple = tuple(documents)
    revision = Revision(
        revision_id="pg-search-route-integration",
        source_revision="catalog-fixture-r1",
        embedding_profile_id=PROFILE.profile_id,
        chunker_version="integration-v1",
        dictionary_version="questions-1",
        config_hash=text_hash("pg-search-route-integration"),
        document_hashes=tuple(
            sorted(((item.document_id, item.digest()) for item in document_tuple), key=str)
        ),
        chunk_count=len(chunks),
        embedding_count=len(embeddings),
    )
    return revision, document_tuple, tuple(chunks), tuple(embeddings)


@pytest.fixture
def search_case(
    db: psycopg.Connection[tuple[object, ...]], dsn: str
) -> SearchCase:
    extension = db.execute(
        "SELECT extversion FROM pg_extension WHERE extname='pg_search'"
    ).fetchone()
    if extension is None or extension[0] != "0.27.0":
        pytest.skip("requires the PostgreSQL 17 + pgvector + pg_search 0.27.0 image")
    migration = ROOT / "migrations" / "ai" / "004_pg_search_bm25.sql"
    db.execute(migration.read_text(encoding="utf-8"))
    store = PostgresCorpusStore(dsn)
    revision, documents, chunks, embeddings = _bundle()
    assert store.stage(revision, documents, chunks, embeddings)
    store.activate(
        revision.revision_id,
        manifest_hash=revision.manifest_hash,
        expected_active=None,
        expected_revocation_sequence=0,
    )
    return SearchCase(store)


def _filters(**changes: object) -> HardFilters:
    values: dict[str, object] = {
        "filterHash": "sha256:" + "b" * 64,
        "publicOnly": True,
        "placeIds": None,
        "regionCodes": None,
        "categoryCodes": ("HANOK",),
        "pinnedPlaceIds": (),
        "excludedPlaceIds": (),
    }
    values.update(changes)
    return HardFilters.model_validate(values)


def _lexical_request(snapshot: CorpusSnapshot, **filter_changes: object) -> LexicalRequest:
    return LexicalRequest.model_validate(
        {
            "runId": RUN_ID,
            "planHash": PLAN_HASH,
            "versions": snapshot.versions,
            "query": "북촌 한옥마을",
            "filters": _filters(**filter_changes),
            "indexVersion": "ko-bm25-v1",
        }
    )


def _approved_plan(snapshot: CorpusSnapshot, mode: str) -> ApprovedQueryPlan:
    fixture = ROOT / "tests" / "contracts" / "fixtures" / "accepted-approved-hybrid.json"
    payload = json.loads(fixture.read_text(encoding="utf-8"))["payload"]
    plan = ApprovedQueryPlan.model_validate(payload)
    filters = _filters()
    return plan.model_copy(
        update={
            "approved_retrieval_mode": mode,
            "approved_filters": filters,
            "semantic_query": "북촌 한옥마을",
            "versions": snapshot.versions,
        }
    )


def _vector_searcher(*, output_dimensions: int = 384) -> VectorSearcher:
    service = EmbeddingService(FixedBackend(output_dimensions=output_dimensions), profile=PROFILE)
    return VectorSearcher(service)


def test_pg_search_lexical_korean_filters_and_topk_order(search_case: SearchCase) -> None:
    with search_case.store.snapshot() as snapshot:
        candidates = LexicalSearchAdapter(PostgresLexicalChunkRepository()).search(
            _lexical_request(snapshot), snapshot
        )
    assert candidates.candidates
    assert all(item.source_id != "p-tourapi-museum" for item in candidates.candidates)
    scores = [item.score for item in candidates.candidates]
    assert scores == sorted(scores, reverse=True)
    assert len(candidates.candidates) <= 20


def test_pgvector_dense_route_filters_and_topk(search_case: SearchCase) -> None:
    with search_case.store.snapshot() as snapshot:
        result = _vector_searcher().search(
            snapshot,
            "북촌 한옥마을",
            filters=VectorSearchFilters(category_codes=frozenset({"HANOK"})),
            limit=20,
        )
    assert result
    assert result[0].source_id == "p-tourapi-bukchon"
    assert result[0].score >= result[-1].score
    assert len(result) <= 20


@pytest.mark.parametrize("mode", ["LEXICAL_ONLY", "DENSE_ONLY", "HYBRID"])
def test_search_router_executes_database_retrieval_modes(
    search_case: SearchCase, mode: str
) -> None:
    with search_case.store.snapshot() as snapshot:
        coordinator = HybridRetrievalCoordinator(
            lexical_searcher=LexicalSearchAdapter(PostgresLexicalChunkRepository()),
            dense_searcher=_vector_searcher(),
        )
        result = coordinator.execute(
            HybridSearchRequest(plan=_approved_plan(snapshot, mode)), snapshot
        )
    assert result.candidates
    if mode == "HYBRID":
        assert result.stage == "FUSION"
    else:
        assert result.stage == ("LEXICAL" if mode == "LEXICAL_ONLY" else "DENSE")


def test_postgres_routes_return_empty_for_hard_filter_miss(search_case: SearchCase) -> None:
    with search_case.store.snapshot() as snapshot:
        lexical = LexicalSearchAdapter(PostgresLexicalChunkRepository()).search(
            _lexical_request(snapshot, placeIds=("p-tourapi-missing",)), snapshot
        )
        dense = _vector_searcher().search(
            snapshot,
            "북촌 한옥마을",
            filters=VectorSearchFilters(place_ids=frozenset({"p-tourapi-missing"})),
        )
    assert not lexical.candidates
    assert not dense


def test_pgvector_query_dimension_mismatch_fails_closed(search_case: SearchCase) -> None:
    with (
        search_case.store.snapshot() as snapshot,
        pytest.raises(VectorSearchError, match="DIMENSION_MISMATCH"),
    ):
        _vector_searcher(output_dimensions=3).search(snapshot, "북촌 한옥마을")
