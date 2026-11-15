"""Pinned embedding profiles and fail-closed embedding execution."""

from .service import (
    E5_SMALL_384,
    GEMINI_EMBEDDING_384,
    DeterministicHashBackend,
    EmbeddingBackend,
    EmbeddingError,
    EmbeddingMetrics,
    EmbeddingMetricSample,
    EmbeddingProfile,
    EmbeddingService,
    EmbeddingWorkGate,
    GeminiEmbeddingBackend,
    InMemoryEmbeddingMetrics,
)

__all__ = [
    "DeterministicHashBackend",
    "E5_SMALL_384",
    "GEMINI_EMBEDDING_384",
    "EmbeddingBackend",
    "EmbeddingError",
    "EmbeddingMetricSample",
    "EmbeddingMetrics",
    "EmbeddingProfile",
    "EmbeddingService",
    "EmbeddingWorkGate",
    "GeminiEmbeddingBackend",
    "InMemoryEmbeddingMetrics",
]
