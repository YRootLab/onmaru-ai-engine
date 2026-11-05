"""Evidence selection and place diversity caps (W11)."""

from __future__ import annotations

import logging
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Protocol

from onmaru_ai.contracts.models import CandidateSet, Evidence, EvidenceSet

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
            start_offset, end_offset = (0, 100)
            if self._chunk_lookup is not None:
                try:
                    start_offset, end_offset = self._chunk_lookup.get_span(chunk_id)
                except Exception as e:
                    logger.warning("Could not lookup span for chunk %s: %s", chunk_id, e)

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
