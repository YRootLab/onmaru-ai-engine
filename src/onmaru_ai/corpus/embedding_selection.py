"""Safe selection of semantic versus local-only corpus embedding backends."""

from __future__ import annotations

from onmaru_ai.embedding import (
    DETERMINISTIC_HASH_384,
    E5_SMALL_ONNX_INT8_384,
    DeterministicHashBackend,
    EmbeddingBackend,
    EmbeddingProfile,
    OnnxE5EmbeddingBackend,
)


def select_embedding_backend(
    *, model_dir: str, hash_only: bool, dry_run: bool
) -> tuple[EmbeddingBackend, EmbeddingProfile]:
    if hash_only:
        if not dry_run:
            raise ValueError("--hash-only requires --dry-run and cannot stage a corpus")
        return DeterministicHashBackend(), DETERMINISTIC_HASH_384
    if not model_dir.strip():
        raise ValueError("ONMARU_E5_ONNX_DIR is required for local E5 embeddings")
    backend = OnnxE5EmbeddingBackend(model_dir)
    return backend, E5_SMALL_ONNX_INT8_384
