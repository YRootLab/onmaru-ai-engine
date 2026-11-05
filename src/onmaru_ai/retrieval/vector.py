from __future__ import annotations

import math
from dataclasses import dataclass
from uuid import UUID

from onmaru_ai.embedding import EmbeddingError, EmbeddingService
from onmaru_ai.storage.postgres import CorpusSnapshot


class VectorSearchError(RuntimeError):
    """Dense retrieval crossed an approved snapshot or filter boundary."""


@dataclass(frozen=True)
class VectorSearchFilters:
    place_ids: frozenset[UUID] = frozenset()
    region_codes: frozenset[str] = frozenset()
    category_codes: frozenset[str] = frozenset()


@dataclass(frozen=True)
class VectorCandidate:
    place_id: UUID
    document_id: UUID
    chunk_id: UUID
    source_type: str
    source_id: str
    source_revision: str
    score: float
    rank: int
    corpus_revision: str
    embedding_profile_id: str
    dictionary_version: str
    source_revocation_sequence: int


class VectorSearcher:
    """Exact cosine pgvector adapter constrained to one CorpusSnapshot."""

    def __init__(self, embeddings: EmbeddingService) -> None:
        self._embeddings = embeddings

    def search(
        self,
        snapshot: CorpusSnapshot,
        semantic_query: str,
        *,
        filters: VectorSearchFilters | None = None,
        limit: int = 20,
    ) -> tuple[VectorCandidate, ...]:
        filters = filters or VectorSearchFilters()
        if not 1 <= limit <= 20:
            raise VectorSearchError("LIMIT_OUT_OF_RANGE")
        if snapshot.embedding_profile_id != self._embeddings.profile.profile_id:
            raise VectorSearchError("PROFILE_MISMATCH")
        try:
            query_vector = self._embeddings.embed_query(semantic_query)
        except EmbeddingError as error:
            raise VectorSearchError(str(error)) from error

        clauses = [
            "d.revision_id = %s",
            "e.embedding_profile_id = %s",
            "d.eligibility_status = 'PUBLIC'",
            "NOT EXISTS (SELECT 1 FROM ai.place_revocations pr WHERE pr.place_id=d.place_id)",
            "NOT EXISTS (SELECT 1 FROM ai.source_revocations sr WHERE "
            "(sr.source_type,sr.source_id,sr.source_revision)="
            "(d.source_type,d.source_id,d.source_revision))",
        ]
        vector = list(query_vector)
        # Placeholder order follows SQL text: SELECT distance, WHERE snapshot/filters,
        # ORDER BY distance, LIMIT.
        parameters: list[object] = [
            vector,
            snapshot.versions.corpus_revision,
            snapshot.embedding_profile_id,
        ]
        if filters.place_ids:
            clauses.append("d.place_id = ANY(%s)")
            parameters.append(list(sorted(filters.place_ids, key=str)))
        if filters.region_codes:
            clauses.append("d.region_code = ANY(%s)")
            parameters.append(sorted(filters.region_codes))
        if filters.category_codes:
            clauses.append("d.category_code = ANY(%s)")
            parameters.append(sorted(filters.category_codes))
        parameters.extend((vector, limit))
        statement = f"""
            SELECT d.place_id, d.document_id, c.chunk_id, d.source_type, d.source_id,
                   d.source_revision, 1 - (e.embedding <=> %s::vector) AS score
              FROM ai.embeddings e
              JOIN ai.chunks c USING (revision_id, chunk_id)
              JOIN ai.documents d USING (revision_id, document_id)
             WHERE {' AND '.join(clauses)}
             ORDER BY e.embedding <=> %s::vector, c.chunk_id
             LIMIT %s
        """
        rows = snapshot.connection.execute(statement, tuple(parameters)).fetchall()
        return self._validate_rows(snapshot, filters, rows, limit)

    def _validate_rows(
        self,
        snapshot: CorpusSnapshot,
        filters: VectorSearchFilters,
        rows: list[dict[str, object]],
        limit: int,
    ) -> tuple[VectorCandidate, ...]:
        if len(rows) > limit:
            raise VectorSearchError("INVALID_SEARCH_RESULT")
        seen: set[UUID] = set()
        candidates: list[VectorCandidate] = []
        for rank, row in enumerate(rows, 1):
            try:
                place_id = UUID(str(row["place_id"]))
                chunk_id = UUID(str(row["chunk_id"]))
                raw_score = row["score"]
                if isinstance(raw_score, bool) or not isinstance(raw_score, (int, float)):
                    raise ValueError
                score = float(raw_score)
                source = (
                    str(row["source_type"]),
                    str(row["source_id"]),
                    str(row["source_revision"]),
                )
                if chunk_id in seen or not math.isfinite(score) or not -1.0 <= score <= 1.0:
                    raise ValueError
                if (
                    place_id in snapshot.revoked_places
                    or source in snapshot.revoked_sources
                    or (filters.place_ids and place_id not in filters.place_ids)
                ):
                    raise VectorSearchError("RESULT_OUTSIDE_FILTERS")
                seen.add(chunk_id)
                candidates.append(
                    VectorCandidate(
                        place_id=place_id,
                        document_id=UUID(str(row["document_id"])),
                        chunk_id=chunk_id,
                        source_type=source[0],
                        source_id=source[1],
                        source_revision=source[2],
                        score=score,
                        rank=rank,
                        corpus_revision=snapshot.versions.corpus_revision,
                        embedding_profile_id=snapshot.embedding_profile_id,
                        dictionary_version=snapshot.versions.question_dictionary_version,
                        source_revocation_sequence=snapshot.versions.source_revocation_sequence,
                    )
                )
            except VectorSearchError:
                raise
            except (KeyError, TypeError, ValueError, OverflowError) as error:
                raise VectorSearchError("INVALID_SEARCH_RESULT") from error
        return tuple(candidates)
