"""Pinned embedding profiles and fail-closed embedding execution."""

from .service import (
    E5_SMALL_384,
    EmbeddingBackend,
    EmbeddingError,
    EmbeddingMetrics,
    EmbeddingMetricSample,
    EmbeddingProfile,
    EmbeddingService,
    EmbeddingWorkGate,
    InMemoryEmbeddingMetrics,
)

__all__ = [
    "E5_SMALL_384",
    "EmbeddingBackend",
    "EmbeddingError",
    "EmbeddingMetricSample",
    "EmbeddingMetrics",
    "EmbeddingProfile",
    "EmbeddingService",
    "EmbeddingWorkGate",
    "InMemoryEmbeddingMetrics",
]
