"""Evidence selection and place diversity caps (W11)."""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from onmaru_ai.contracts.models import ApprovedQueryPlan, CandidateSet, Evidence, EvidenceSet
from onmaru_ai.storage.postgres import CorpusSnapshot

logger = logging.getLogger(__name__)


class ChunkSpanLookup(Protocol):
    """Protocol for fetching active source snapshot offsets for a chunk."""

    def get_span(self, chunk_id: str) -> tuple[int, int]: ...


@dataclass(frozen=True, slots=True)
class EvidenceSelectorConfig:
    max_total_evidence: int = 12
    max_evidence_per_place: int = 2


class EvidenceSelector:
    """
    Selects up to 12 evidence items with at most 2 chunks per place,
    preserving rank order and source traceability.
    """

    def __init__(
        self,
        *,
        chunk_lookup: ChunkSpanLookup | None = None,
        max_total: int = 12,
        max_per_place: int = 2,
    ) -> None:
        self._chunk_lookup = chunk_lookup
        self._max_total = max_total
        self._max_per_place = max_per_place

    def select_evidence(
        self,
        candidate_set: CandidateSet,
        ranked_candidates: Sequence[Mapping[str, Any]],
        *,
        snapshot: CorpusSnapshot | None = None,
    ) -> EvidenceSet:
        selected_evidence: list[Evidence] = []
        place_counts: Counter[str] = Counter()

        for cand in ranked_candidates:
            if len(selected_evidence) >= self._max_total:
                break

            place_id = str(cand["place_id"])
            if place_counts[place_id] >= self._max_per_place:
                continue

            chunk_id = str(cand["chunk_id"])
            if self._chunk_lookup is not None:
                try:
                    start_offset, end_offset = self._chunk_lookup.get_span(chunk_id)
                except Exception as e:
                    logger.warning("Could not lookup span for chunk %s: %s", chunk_id, e)
                    continue
            elif snapshot is not None:
                try:
                    rows = snapshot.connection.execute(
                        """SELECT f.start_offset, f.end_offset, f.fact_text, d.normalized_text
                         FROM ai.reviewed_facts f
                         JOIN ai.chunks c USING (revision_id, chunk_id)
                         JOIN ai.documents d USING (revision_id, document_id)
                        WHERE f.revision_id=%s AND f.chunk_id=%s
                          AND f.place_id=%s AND d.source_id=f.place_id
                          AND d.source_id=%s AND d.source_revision=%s
                          AND f.review_status='APPROVED'
                          AND f.start_offset >= c.start_offset
                          AND f.end_offset <= c.end_offset
                          AND d.eligibility_status='PUBLIC'
                            ORDER BY f.fact_id""",
                        (
                            snapshot.versions.corpus_revision,
                            chunk_id,
                            str(cand["place_id"]),
                            str(cand["place_id"]),
                            str(cand["source_revision"]),
                        ),
                    ).fetchall()
                except Exception:
                    logger.warning("Reviewed fact lookup unavailable; evidence selection skipped")
                    continue
                row = next(
                    (
                        item
                        for item in rows
                        if item["normalized_text"][item["start_offset"]:item["end_offset"]]
                        == item["fact_text"]
                    ),
                    None,
                )
                if row is None:
                    continue
                start_offset, end_offset = int(row["start_offset"]), int(row["end_offset"])
            else:
                # Never mint evidence with guessed offsets.
                continue

            if end_offset <= start_offset:
                end_offset = start_offset + 1

            evidence_id = f"ev-{len(selected_evidence) + 1}"
            ev = Evidence.model_validate(
                {
                    "evidenceId": evidence_id,
                    "chunkId": chunk_id,
                    "placeId": place_id,
                    "sourceId": str(cand["source_id"]),
                    "sourceRevision": str(cand["source_revision"]),
                    "startOffset": start_offset,
                    "endOffset": end_offset,
                }
            )
            selected_evidence.append(ev)
            place_counts[place_id] += 1

        allowed_places = tuple(sorted({e.place_id for e in selected_evidence}))

        return EvidenceSet.model_validate(
            {
                "schemaVersion": "ai-evidence-set.v1",
                "runId": candidate_set.run_id,
                "planHash": candidate_set.plan_hash,
                "versions": candidate_set.versions,
                "allowedPlaceIds": allowed_places,
                "evidence": tuple(selected_evidence),
            }
        )

    def select_for_places(
        self,
        plan: ApprovedQueryPlan,
        place_ids: Sequence[str],
        *,
        snapshot: CorpusSnapshot,
    ) -> EvidenceSet:
        """Select reviewed corpus facts for places returned by an approved SQL lookup.

        This is a SQL_PLUS_RETRIEVAL fallback when retrieval returned no evidence. It
        never treats Spring's place projection as evidence: every span comes from an
        approved fact bound to the current public corpus snapshot.
        """
        filters = plan.approved_filters
        requested = tuple(dict.fromkeys(place_ids))
        if plan.approved_route != "SQL_PLUS_RETRIEVAL":
            raise ValueError("SQL-derived evidence is only valid for SQL_PLUS_RETRIEVAL")
        if filters.place_ids is not None:
            requested = tuple(place_id for place_id in requested if place_id in filters.place_ids)
        requested = tuple(
            place_id for place_id in requested if place_id not in filters.excluded_place_ids
        )
        if not requested:
            return _evidence_set(plan, snapshot, ())

        rows = snapshot.connection.execute(
            """SELECT f.fact_id, f.chunk_id, f.place_id, f.start_offset, f.end_offset,
                      f.fact_text, d.place_id AS corpus_place_uuid, d.source_id,
                      d.source_revision, d.source_type, d.region_code, d.category_code,
                      d.eligibility_status, d.normalized_text, c.start_offset AS chunk_start,
                      c.end_offset AS chunk_end, c.chunk_text
                 FROM ai.reviewed_facts f
                 JOIN ai.chunks c USING (revision_id, chunk_id)
                 JOIN ai.documents d USING (revision_id, document_id)
                WHERE f.revision_id=%s AND f.place_id = ANY(%s)
                  AND f.review_status='APPROVED' AND d.source_id=f.place_id
                  AND d.eligibility_status='PUBLIC'
                ORDER BY f.place_id, f.fact_id""",
            (snapshot.versions.corpus_revision, list(requested)),
        ).fetchall()

        selected: list[Evidence] = []
        counts: Counter[str] = Counter()
        selected_chunks: set[str] = set()
        region_codes = (
            {value.casefold() for value in filters.region_codes}
            if filters.region_codes is not None
            else None
        )
        category_codes = (
            {value.casefold() for value in filters.category_codes}
            if filters.category_codes is not None
            else None
        )
        revoked_places = {str(place_id) for place_id in snapshot.revoked_places}
        revoked_sources = set(snapshot.revoked_sources)
        for row in rows:
            place_id = str(row["place_id"])
            chunk_id = str(row["chunk_id"])
            region_code = str(row["region_code"] or "").casefold()
            category_code = str(row["category_code"] or "").casefold()
            if (
                place_id not in requested
                or place_id in filters.excluded_place_ids
                or (filters.place_ids is not None and place_id not in filters.place_ids)
                or counts[place_id] >= self._max_per_place
                or len(selected) >= self._max_total
                or chunk_id in selected_chunks
                or str(row["corpus_place_uuid"]) in revoked_places
                or (row["source_type"], row["source_id"], row["source_revision"])
                in revoked_sources
                or (region_codes is not None and region_code not in region_codes)
                or (category_codes is not None and category_code not in category_codes)
            ):
                continue
            start, end = int(row["start_offset"]), int(row["end_offset"])
            chunk_start, chunk_end = int(row["chunk_start"]), int(row["chunk_end"])
            normalized_text = row["normalized_text"]
            if (
                start < chunk_start
                or end > chunk_end
                or normalized_text[start:end] != row["fact_text"]
                or row["chunk_text"] != normalized_text[chunk_start:chunk_end]
            ):
                continue
            selected.append(
                Evidence.model_validate(
                    {
                        "evidenceId": f"ev-sql-{len(selected) + 1}",
                        "chunkId": chunk_id,
                        "placeId": place_id,
                        "sourceId": str(row["source_id"]),
                        "sourceRevision": str(row["source_revision"]),
                        "startOffset": start,
                        "endOffset": end,
                    }
                )
            )
            counts[place_id] += 1
            selected_chunks.add(chunk_id)
        return _evidence_set(plan, snapshot, tuple(selected))


def _evidence_set(
    plan: ApprovedQueryPlan,
    snapshot: CorpusSnapshot,
    evidence: tuple[Evidence, ...],
) -> EvidenceSet:
    return EvidenceSet.model_validate(
        {
            "schemaVersion": "ai-evidence-set.v1",
            "runId": plan.run_id,
            "planHash": plan.approved_plan_hash,
            "versions": snapshot.versions,
            "allowedPlaceIds": tuple(sorted({item.place_id for item in evidence})),
            "evidence": evidence,
        }
    )
