from __future__ import annotations

import pytest

from onmaru_ai.corpus.embedding_selection import select_embedding_backend
from onmaru_ai.embedding import (
    DETERMINISTIC_HASH_384,
    GEMINI_EMBEDDING_384,
    DeterministicHashBackend,
)


def test_ingestion_requires_gemini_key_unless_hash_mode_is_explicit() -> None:
    with pytest.raises(ValueError, match="Gemini API key is required"):
        select_embedding_backend(
            api_key="", hash_only=False, dry_run=False
        )


def test_ingestion_selects_gemini_backend_when_key_is_present() -> None:
    backend, profile = select_embedding_backend(
        api_key="test-key", hash_only=False, dry_run=False
    )

    assert backend.model_id == GEMINI_EMBEDDING_384.model_id
    assert profile == GEMINI_EMBEDDING_384


def test_explicit_hash_mode_uses_nonsemantic_profile_and_cannot_activate() -> None:
    backend, profile = select_embedding_backend(
        api_key="", hash_only=True, dry_run=True
    )

    assert isinstance(backend, DeterministicHashBackend)
    assert profile == DETERMINISTIC_HASH_384
    assert profile != GEMINI_EMBEDDING_384

    with pytest.raises(ValueError, match="requires --dry-run"):
        select_embedding_backend(api_key="", hash_only=True, dry_run=False)
