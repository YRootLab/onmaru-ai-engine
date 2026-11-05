"""Closed lexical retrieval adapter over an active PostgreSQL corpus snapshot."""

from __future__ import annotations

import re
import time
import unicodedata
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated, Literal, Protocol
from uuid import UUID

from pydantic import Field

from onmaru_ai.contracts.models import (
    Candidate,
    CandidateSet,
    ClosedModel,
    Digest,
    HardFilters,
    RunId,
    Versions,
)
from onmaru_ai.corpus.bm25 import KoreanBm25, KoreanTokenizer
from onmaru_ai.storage.postgres import CorpusSnapshot

BM25_LIMIT = 20
SUPPORTED_INDEX_VERSION = "ko-bm25-v1"
_NON_NAME = re.compile(r"[^0-9a-z가-힣]")


class LexicalIndexError(RuntimeError):
    """The lexical index cannot safely serve the requested snapshot."""


class LexicalRequest(ClosedModel):
    run_id: RunId
    plan_hash: Digest
    versions: Versions
    query: Annotated[str, Field(min_length=1, max_length=240)]
    filters: HardFilters
    index_version: Literal["ko-bm25-v1"]


@dataclass(frozen=True)
class LexicalChunk:
    chunk_id: str
    place_id: str
    source_id: str
    source_revision: str
    corpus_revision: str
    region_code: str
    category_code: str
    text: str
    exact_names: tuple[str, ...]
    public: bool
    source_type: str = "TOUR_API"


class LexicalChunkRepository(Protocol):
    def load(
        self, snapshot: CorpusSnapshot, request: LexicalRequest
    ) -> tuple[LexicalChunk, ...]: ...


class PostgresLexicalChunkRepository:
    """Read lexical inputs through the caller-owned repeatable-read snapshot.

    ``pg_search`` availability is checked explicitly. The SQL projection currently
    uses the public document title as an exact name; reviewed aliases can be supplied
    by extending the projection without changing the scoring contract.
    """

    def __init__(self, *, index_version: str = SUPPORTED_INDEX_VERSION) -> None:
        if not index_version.strip():
            raise ValueError("index_version must not be blank")
        self._index_version = index_version

    def load(
        self, snapshot: CorpusSnapshot, request: LexicalRequest
    ) -> tuple[LexicalChunk, ...]:
        extension = snapshot.connection.execute(
            "SELECT extversion FROM pg_extension WHERE extname='pg_search'"
        ).fetchone()
        if extension is None:
            raise LexicalIndexError("BM25_EXTENSION_UNAVAILABLE")
        if request.index_version != self._index_version:
            raise LexicalIndexError("BM25_INDEX_VERSION_MISMATCH")
        rows = snapshot.connection.execute(
            """SELECT c.chunk_id, d.place_id, d.source_type, d.source_id,
                      d.source_revision, c.revision_id AS corpus_revision,
                      d.region_code, d.category_code, c.search_text AS text,
                      d.title, d.eligibility_status
                 FROM ai.chunks c
                 JOIN ai.documents d USING (revision_id, document_id)
                WHERE c.revision_id=%s AND d.eligibility_status='PUBLIC'""",
            (snapshot.versions.corpus_revision,),
        )
        return tuple(
            LexicalChunk(
                chunk_id=str(row["chunk_id"]),
                place_id=str(row["place_id"]),
                source_type=str(row["source_type"]),
                source_id=str(row["source_id"]),
                source_revision=str(row["source_revision"]),
                corpus_revision=str(row["corpus_revision"]),
                region_code=str(row["region_code"]),
                category_code=str(row["category_code"]),
                text=str(row["text"]),
                exact_names=(str(row["title"]),),
                public=row["eligibility_status"] == "PUBLIC",
            )
            for row in rows
        )


class LexicalSearchAdapter:
    def __init__(
        self,
        repository: LexicalChunkRepository,
        *,
        tokenizer: KoreanTokenizer | None = None,
        scorer: KoreanBm25 | None = None,
        clock_ns: Callable[[], int] = time.monotonic_ns,
    ) -> None:
        self._repository = repository
        self._tokenizer = tokenizer or KoreanTokenizer()
        self._scorer = scorer or KoreanBm25()
        self._clock_ns = clock_ns

    def search(self, request: LexicalRequest, snapshot: CorpusSnapshot) -> CandidateSet:
        started = self._clock_ns()
        if request.versions != snapshot.versions:
            raise LexicalIndexError("CORPUS_SNAPSHOT_VERSION_MISMATCH")
        chunks = tuple(
            chunk
            for chunk in self._repository.load(snapshot, request)
            if self._eligible(chunk, request, snapshot)
        )
        query_tokens = self._tokenizer.tokenize(request.query)
        tokenized = tuple(self._tokenizer.tokenize(chunk.text) for chunk in chunks)
        scores = self._scorer.score(query_tokens, tokenized)
        query_name = _normalize_name(request.query, self._tokenizer)
        ranked = []
        for chunk, score in zip(chunks, scores, strict=True):
            exact = any(
                _name_matches(query_name, _normalize_name(name, self._tokenizer))
                for name in chunk.exact_names
            )
            if score > 0 or exact:
                ranked.append((not exact, -score, chunk.chunk_id, chunk, score))
        ranked.sort(key=lambda item: item[:3])
        candidates = tuple(
            Candidate.model_validate(
                {
                    "chunkId": item[3].chunk_id,
                    "placeId": item[3].place_id,
                    "sourceId": item[3].source_id,
                    "sourceRevision": item[3].source_revision,
                    "rank": rank,
                    "score": item[4],
                    "exclusionReason": None,
                }
            )
            for rank, item in enumerate(ranked[:BM25_LIMIT], start=1)
        )
        elapsed_ms = max(0, (self._clock_ns() - started) // 1_000_000)
        return CandidateSet.model_validate(
            {
                "schemaVersion": "ai-candidate-set.v1",
                "runId": request.run_id,
                "planHash": request.plan_hash,
                "versions": request.versions,
                "stage": "LEXICAL",
                "candidates": candidates,
                "retrievalStatus": "COMPLETE" if candidates else "NO_EVIDENCE",
                "latencyMs": elapsed_ms,
            }
        )

    @staticmethod
    def _eligible(
        chunk: LexicalChunk, request: LexicalRequest, snapshot: CorpusSnapshot
    ) -> bool:
        filters = request.filters
        try:
            place_uuid = UUID(chunk.place_id)
        except ValueError:
            return False
        return (
            chunk.public
            and chunk.corpus_revision == snapshot.versions.corpus_revision
            and place_uuid not in snapshot.revoked_places
            and (chunk.source_type, chunk.source_id, chunk.source_revision)
            not in snapshot.revoked_sources
            and chunk.place_id not in filters.excluded_place_ids
            and (filters.place_ids is None or chunk.place_id in filters.place_ids)
            and (filters.region_codes is None or chunk.region_code in filters.region_codes)
            and (filters.category_codes is None or chunk.category_code in filters.category_codes)
        )


def _normalize_name(value: str, tokenizer: KoreanTokenizer) -> str:
    return _NON_NAME.sub("", "".join(tokenizer.tokenize(unicodedata.normalize("NFKC", value))))


def _name_matches(query: str, name: str) -> bool:
    return bool(query and name and (query.startswith(name) or name.startswith(query)))
