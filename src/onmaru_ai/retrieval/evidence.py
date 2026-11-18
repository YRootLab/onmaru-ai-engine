"""Evidence selection and place diversity caps (W11)."""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from onmaru_ai.contracts.models import CandidateSet, Evidence, EvidenceSet
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
