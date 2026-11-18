"""Safe selection of semantic versus local-only corpus embedding backends."""

from __future__ import annotations

import time

from onmaru_ai.embedding import (
    DETERMINISTIC_HASH_384,
    GEMINI_EMBEDDING_384,
    DeterministicHashBackend,
    EmbeddingBackend,
    EmbeddingProfile,
    GeminiEmbeddingBackend,
)


class RetryingGeminiEmbeddingBackend:
    def __init__(self, inner: GeminiEmbeddingBackend, max_retries: int = 5) -> None:
        self._inner = inner
        self._max_retries = max_retries
        self.model_id = inner.model_id
        self.model_commit = inner.model_commit
        self.dimensions = inner.dimensions

    def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        delay = 1.0
        for attempt in range(1, self._max_retries + 1):
            try:
                return self._inner.encode(texts)
            except Exception:
                if attempt == self._max_retries:
                    raise
                time.sleep(delay)
                delay = min(delay * 2.0, 20.0)
        raise RuntimeError("unreachable")


def select_embedding_backend(
    *, api_key: str, hash_only: bool, dry_run: bool
) -> tuple[EmbeddingBackend, EmbeddingProfile]:
    if hash_only:
        if not dry_run:
            raise ValueError("--hash-only requires --dry-run and cannot stage a corpus")
        return DeterministicHashBackend(), DETERMINISTIC_HASH_384
    if not api_key.strip():
        raise ValueError("Gemini API key is required unless --hash-only --dry-run is selected")
    backend = GeminiEmbeddingBackend(
        api_key, task_type="RETRIEVAL_DOCUMENT", timeout_seconds=30.0
    )
    return RetryingGeminiEmbeddingBackend(backend), GEMINI_EMBEDDING_384
