"""Lightweight reranker with deterministic fallback (W11)."""

from __future__ import annotations

import concurrent.futures
import logging
import math
import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class RerankerError(Exception):
    """Base error for reranker failure."""


class RerankerTimeoutError(RerankerError):
    """Raised when reranker times out."""


@dataclass(frozen=True, slots=True)
class RerankerConfig:
    timeout_seconds: float = 0.5
    fallback_to_candidate_order: bool = True


class DeterministicSemanticCrossScorer:
    """Fast, deterministic CPU cross-scorer based on character/token overlap and base score.

    Used when a heavy neural cross-encoder is not configured, guaranteeing zero model loading
    overhead, zero OOM risk, and <1ms execution on 30 candidates.
    """

    def __init__(self, *, text_lookup: Callable[[str], str | None] | None = None) -> None:
        self._text_lookup = text_lookup

    def __call__(self, query: str, candidates: Sequence[Mapping[str, Any]]) -> Sequence[float]:
        if not candidates:
            return ()
        q_norm = query.strip().lower()
        q_tokens = set(re.findall(r"[\w가-힣]+", q_norm))
        q_bigrams = (
            {q_norm[i : i + 2] for i in range(len(q_norm) - 1)} if len(q_norm) >= 2 else set(q_norm)
        )

        scores: list[float] = []
        for cand in candidates:
            base_score = float(cand.get("score", 0.0))
            text = cand.get("chunk_text") or cand.get("text")
            if not text and self._text_lookup:
                chunk_id = str(cand.get("chunk_id", ""))
                if chunk_id:
                    text = self._text_lookup(chunk_id)

            if not text:
                scores.append(base_score)
                continue

            t_norm = str(text).strip().lower()
            t_tokens = set(re.findall(r"[\w가-힣]+", t_norm))
            t_bigrams = (
                {t_norm[i : i + 2] for i in range(len(t_norm) - 1)}
                if len(t_norm) >= 2
                else set(t_norm)
            )

            token_overlap = len(q_tokens & t_tokens) / max(1, len(q_tokens))
            bigram_overlap = len(q_bigrams & t_bigrams) / max(1, len(q_bigrams))

            # Composite cross-relevance score combining lexical precision + base RRF rank
            cross_score = (
                0.5 * token_overlap + 0.3 * bigram_overlap + 0.2 * min(1.0, max(0.0, base_score))
            )
            scores.append(round(cross_score, 6))
        return scores


class OnnxCrossEncoderScorer:
    """Dynamic-int8 ONNX Cross-Encoder scorer."""

    def __init__(
        self,
        model_dir: str | Path,
        *,
        text_lookup: Callable[[str], str | None] | None = None,
        max_length: int = 256,
        intra_op_threads: int = 1,
    ) -> None:
        root = Path(model_dir)
        model_path = root / "model.onnx"
        tokenizer_path = root / "tokenizer.json"
        if not model_path.is_file() or not tokenizer_path.is_file():
            raise RerankerError(f"Cross-encoder ONNX artifact incomplete in {root}")

        import numpy as np  # noqa: F401
        import onnxruntime as ort  # type: ignore[import-untyped]
        from tokenizers import Tokenizer  # type: ignore[import-untyped]

        self._tokenizer = Tokenizer.from_file(str(tokenizer_path))
        self._tokenizer.enable_truncation(max_length=max_length)
        self._tokenizer.enable_padding(length=max_length)

        options = ort.SessionOptions()
        options.intra_op_num_threads = max(1, intra_op_threads)
        options.inter_op_num_threads = 1
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        self._session = ort.InferenceSession(
            str(model_path), sess_options=options, providers=["CPUExecutionProvider"]
        )
        self._text_lookup = text_lookup

    def __call__(self, query: str, candidates: Sequence[Mapping[str, Any]]) -> Sequence[float]:
        if not candidates:
            return ()
        import numpy as np

        pairs: list[tuple[str, str]] = []
        for cand in candidates:
            text = cand.get("chunk_text") or cand.get("text")
            if not text and self._text_lookup:
                chunk_id = str(cand.get("chunk_id", ""))
                if chunk_id:
                    text = self._text_lookup(chunk_id)
            pairs.append((query, str(text or "")))

        encoded = self._tokenizer.encode_batch(pairs)
        input_ids = np.array([e.ids for e in encoded], dtype=np.int64)
        attention_mask = np.array([e.attention_mask for e in encoded], dtype=np.int64)

        inputs = {"input_ids": input_ids, "attention_mask": attention_mask}
        # Include token_type_ids if required by model
        input_names = {node.name for node in self._session.get_inputs()}
        if "token_type_ids" in input_names:
            inputs["token_type_ids"] = np.array([e.type_ids for e in encoded], dtype=np.int64)

        outputs = self._session.run(None, inputs)
        logits = outputs[0]
        if logits.ndim > 1:
            logits = logits.squeeze(-1)
        # Apply sigmoid to convert to [0, 1] probability
        scores = 1.0 / (1.0 + np.exp(-logits))
        return [float(s) for s in scores]


def create_production_reranker_scorer(
    environ: Mapping[str, str] | None = None,
    *,
    text_lookup: Callable[[str], str | None] | None = None,
) -> Callable[[str, Sequence[Mapping[str, Any]]], Sequence[float]]:
    source_env = environ if environ is not None else {}
    reranker_dir = source_env.get("ONMARU_RERANKER_ONNX_DIR", "").strip()
    if reranker_dir and Path(reranker_dir).is_dir():
        try:
            return OnnxCrossEncoderScorer(reranker_dir, text_lookup=text_lookup)
        except Exception as e:
            logger.warning(
                "Failed to load ONNX cross-encoder from %s: %s; "
                "falling back to deterministic cross-scorer",
                reranker_dir,
                e,
            )
    return DeterministicSemanticCrossScorer(text_lookup=text_lookup)


def rerank_candidates(
    query: str,
    candidates: Sequence[Mapping[str, Any]],
    *,
    scorer: Callable[[str, Sequence[Mapping[str, Any]]], Sequence[float]] | None = None,
    fallback_on_error: bool = True,
    timeout_seconds: float | None = 0.5,
) -> list[dict[str, Any]]:
    """Reranks candidates using a cross-encoder / lightweight model.

    Falls back deterministically to candidate order on timeout, error, or NaN score.
    """
    if not candidates:
        return []

    original_order = [dict(c, rank=i + 1) for i, c in enumerate(candidates)]

    if scorer is None:
        return original_order

    try:
        if timeout_seconds is not None and timeout_seconds > 0:
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(scorer, query, candidates)
                try:
                    scores = future.result(timeout=timeout_seconds)
                except concurrent.futures.TimeoutError as te:
                    raise RerankerTimeoutError(
                        f"Reranker exceeded {timeout_seconds}s timeout"
                    ) from te
        else:
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
            timeout_seconds=self._config.timeout_seconds,
        )
