"""Pinned embedding profiles and fail-closed embedding execution."""

from .onnx_backend import OnnxE5EmbeddingBackend, load_e5_backend
from .service import (
    DETERMINISTIC_HASH_384,
    E5_SMALL_384,
    E5_SMALL_ONNX_INT8_384,
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
    "DETERMINISTIC_HASH_384",
    "E5_SMALL_384",
    "E5_SMALL_ONNX_INT8_384",
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
    "OnnxE5EmbeddingBackend",
    "load_e5_backend",
]
