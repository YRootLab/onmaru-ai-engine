"""Lightweight reranker with deterministic fallback (W11)."""

from __future__ import annotations

import logging
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


class RerankerError(Exception):
    """Base error for reranker failure."""


class RerankerTimeoutError(RerankerError):
    """Raised when reranker times out."""


@dataclass(frozen=True, slots=True)
class RerankerConfig:
    timeout_seconds: float = 1.0
    fallback_to_candidate_order: bool = True


def rerank_candidates(
    query: str,
    candidates: Sequence[Mapping[str, Any]],
    *,
    scorer: Callable[[str, Sequence[Mapping[str, Any]]], Sequence[float]] | None = None,
    fallback_on_error: bool = True,
) -> list[dict[str, Any]]:
    """
    Reranks candidates using a cross-encoder / lightweight model.
    Falls back deterministically to candidate order on timeout, error, or NaN score.
    """
    if not candidates:
        return []

    original_order = [dict(c, rank=i + 1) for i, c in enumerate(candidates)]

    if scorer is None:
        return original_order

    try:
        scores = scorer(query, candidates)
        if len(scores) != len(candidates):
            raise RerankerError("Score count mismatch")

        # Check for NaN / infinite values
        for s in scores:
            if not isinstance(s, (int, float)) or not math.isfinite(s):
                raise RerankerError(f"Invalid non-finite score from reranker: {s}")

        # Sort candidates descending by model score, tie-break by original rank/chunk_id
        scored_candidates = []
        for orig, score in zip(candidates, scores, strict=True):
            scored_candidates.append((float(score), str(orig["chunk_id"]), orig))

        scored_candidates.sort(key=lambda item: (-item[0], item[1]))

        result: list[dict[str, Any]] = []
        for rank, item in enumerate(scored_candidates, start=1):
            cand_copy = dict(item[2])
            cand_copy["rank"] = rank
            cand_copy["score"] = item[0]
            result.append(cand_copy)
        return result

    except Exception as e:
        logger.warning("Reranker failed, falling back to candidate order: %s", e)
        if fallback_on_error:
            return original_order
        raise RerankerError("Reranking failed without fallback") from e


class Reranker:
    def __init__(
        self,
        *,
        scorer: Callable[[str, Sequence[Mapping[str, Any]]], Sequence[float]] | None = None,
        config: RerankerConfig | None = None,
    ) -> None:
        self._scorer = scorer
        self._config = config or RerankerConfig()

    def rerank(self, query: str, candidates: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
        return rerank_candidates(
            query,
            candidates,
            scorer=self._scorer,
            fallback_on_error=self._config.fallback_to_candidate_order,
        )
