from __future__ import annotations

import math
import resource
import sys
import threading
import time
from collections.abc import Iterator, Sequence
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Protocol

from onmaru_ai.providers.gemini.models import (
    GeminiFailureCode,
    GeminiProviderError,
    retry_after_seconds,
)


class EmbeddingError(RuntimeError):
    """Embedding execution violated the pinned profile or resource boundary."""


@dataclass(frozen=True)
class EmbeddingProfile:
    profile_id: str
    model_id: str
    model_commit: str
    dimensions: int
    passage_prefix: str
    query_prefix: str
    normalization_tolerance: float = 0.0001


# Deployment packaging must resolve this immutable profile to a preloaded artifact. The
# adapter deliberately performs no network download and checks backend identity at startup.
E5_SMALL_384 = EmbeddingProfile(
    profile_id="multilingual-e5-small-384@614241f622f5",
    model_id="intfloat/multilingual-e5-small",
    model_commit="614241f622f53c4eeff9890bdc4f31cfecc418b3",
    dimensions=384,
    passage_prefix="passage: ",
    query_prefix="query: ",
)

E5_SMALL_ONNX_INT8_384 = EmbeddingProfile(
    profile_id="multilingual-e5-small-384-onnx-int8@614241f622f5",
    model_id="intfloat/multilingual-e5-small",
    model_commit="614241f622f53c4eeff9890bdc4f31cfecc418b3:onnx-dynamic-int8-v1",
    dimensions=384,
    passage_prefix="passage: ",
    query_prefix="query: ",
)

DETERMINISTIC_HASH_384 = EmbeddingProfile(
    profile_id="deterministic-hash-384@local-only",
    model_id="deterministic-hash",
    model_commit="local-only",
    dimensions=384,
    passage_prefix="",
    query_prefix="",
)

GEMINI_EMBEDDING_384 = EmbeddingProfile(
    profile_id="gemini-embedding-001-384@v1",
    model_id="gemini-embedding-001",
    model_commit="v1beta-384",
    dimensions=384,
    passage_prefix="",
    query_prefix="",
)


class EmbeddingBackend(Protocol):
    model_id: str
    model_commit: str
    dimensions: int

    def encode(self, texts: tuple[str, ...]) -> Sequence[Sequence[float]]: ...


@dataclass(frozen=True)
class EmbeddingMetricSample:
    operation: str
    temperature: str
    profile_id: str
    batch_size: int
    latency_seconds: float
    rss_bytes: int
    outcome: str


class EmbeddingMetrics(Protocol):
    def record(self, sample: EmbeddingMetricSample) -> None: ...


class InMemoryEmbeddingMetrics:
    def __init__(self) -> None:
        self.samples: list[EmbeddingMetricSample] = []

    def record(self, sample: EmbeddingMetricSample) -> None:
        self.samples.append(sample)


class _NullMetrics:
    def record(self, sample: EmbeddingMetricSample) -> None:
        del sample


class DeterministicHashBackend:
    """Deterministic, CPU-only embedding backend for local pipeline dry-runs.

    Produces normalized, repeatable 384-dimensional vectors via SHA-256 seed expansion.
    Useful only for local pipeline dry-runs; it is not a semantic embedding model.
    """

    model_id: str = DETERMINISTIC_HASH_384.model_id
    model_commit: str = DETERMINISTIC_HASH_384.model_commit
    dimensions: int = 384

    def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        import hashlib

        result: list[tuple[float, ...]] = []
        for text in texts:
            digest = hashlib.sha256(text.encode("utf-8")).digest()
            raw_floats = [
                float((digest[i % len(digest)] - 128) / 128.0) + (0.01 * (i % 7))
                for i in range(self.dimensions)
            ]
            norm = math.sqrt(sum(x * x for x in raw_floats))
            if norm == 0:
                raw_floats[0] = 1.0
                norm = 1.0
            unit_vec = tuple(x / norm for x in raw_floats)
            result.append(unit_vec)
        return tuple(result)


class GeminiEmbeddingBackend:
    """Semantic 384-D embedding backend using Google Gemini gemini-embedding-001."""

    model_id: str = GEMINI_EMBEDDING_384.model_id
    model_commit: str = GEMINI_EMBEDDING_384.model_commit
    dimensions: int = 384

    def __init__(
        self,
        api_key: str,
        *,
        task_type: str = "RETRIEVAL_DOCUMENT",
        timeout_seconds: float = 15.0,
        base_url: str = "https://generativelanguage.googleapis.com/v1beta",
        transport: object | None = None,
    ) -> None:
        if not api_key.strip():
            raise ValueError("api_key must not be blank")
        self._api_key = api_key.strip()
        self._task_type = task_type
        self._timeout_seconds = timeout_seconds
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        import httpx

        if not texts:
            return ()
        url = f"{self._base_url}/models/{self.model_id}:batchEmbedContents"
        payload = {
            "requests": [
                {
                    "model": f"models/{self.model_id}",
                    "content": {"parts": [{"text": text}]},
                    "taskType": self._task_type,
                    "outputDimensionality": self.dimensions,
                }
                for text in texts
            ]
        }
        kwargs: dict[str, object] = {"timeout": self._timeout_seconds}
        if isinstance(self._transport, httpx.BaseTransport):
            kwargs["transport"] = self._transport
        with httpx.Client(**kwargs) as client:  # type: ignore[arg-type]
            response = client.post(
                url,
                headers={"x-goog-api-key": self._api_key},
                json=payload,
            )
            if response.status_code == 429:
                raise GeminiProviderError(
                    GeminiFailureCode.AI_QUOTA_EXCEEDED,
                    retry_after=retry_after_seconds(response.headers),
                )
            response.raise_for_status()
            data = response.json()

        raw_embeddings = data.get("embeddings", [])
        if len(raw_embeddings) != len(texts):
            raise EmbeddingError("GEMINI_EMBEDDING_COUNT_MISMATCH")

        result: list[tuple[float, ...]] = []
        for entry in raw_embeddings:
            values = [float(v) for v in entry.get("values", ())]
            if len(values) != self.dimensions:
                raise EmbeddingError("GEMINI_EMBEDDING_DIM_MISMATCH")
            norm = math.sqrt(sum(v * v for v in values))
            if norm <= 0.0:
                raise EmbeddingError("GEMINI_EMBEDDING_ZERO_NORM")
            result.append(tuple(v / norm for v in values))
        return tuple(result)


class EmbeddingWorkGate:
    """Process-local admission gate separating online queries and offline batches."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._online = 0
        self._batch = False

    @contextmanager
    def online(self) -> Iterator[None]:
        with self._lock:
            if self._batch:
                raise EmbeddingError("ONLINE_EMBEDDING_BUSY")
            self._online += 1
        try:
            yield
        finally:
            with self._lock:
                self._online -= 1

    @contextmanager
    def batch(self) -> Iterator[None]:
        with self._lock:
            if self._batch or self._online:
                raise EmbeddingError("BATCH_DEFERRED")
            self._batch = True
        try:
            yield
        finally:
            with self._lock:
                self._batch = False


class EmbeddingService:
    """Bounded passage/query embedding using one immutable 384-D profile."""

    def __init__(
        self,
        backend: EmbeddingBackend,
        *,
        profile: EmbeddingProfile,
        max_batch_size: int = 32,
        timeout_seconds: float = 10.0,
        metrics: EmbeddingMetrics | None = None,
        work_gate: EmbeddingWorkGate | None = None,
    ) -> None:
        if max_batch_size < 1 or timeout_seconds <= 0:
            raise ValueError("embedding limits must be positive")
        if (
            backend.model_id != profile.model_id
            or backend.model_commit != profile.model_commit
            or backend.dimensions != profile.dimensions
            or profile.dimensions != 384
        ):
            raise EmbeddingError("PROFILE_MISMATCH")
        self._backend = backend
        self.profile = profile
        self._max_batch_size = max_batch_size
        self._timeout_seconds = timeout_seconds
        self._metrics = metrics or _NullMetrics()
        self._work_gate = work_gate or EmbeddingWorkGate()
        # One worker serializes model access and prevents online/batch concurrency inside a
        # process. Deployment admission must additionally serialize offline indexing globally.
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="embedding")
        self._warmed = False

    def embed_passages(self, texts: Sequence[str]) -> tuple[tuple[float, ...], ...]:
        with self._work_gate.batch():
            return self._embed(
                tuple(texts), prefix=self.profile.passage_prefix, operation="passage"
            )

    def embed_query(self, text: str) -> tuple[float, ...]:
        with self._work_gate.online():
            return self._embed((text,), prefix=self.profile.query_prefix, operation="query")[0]

    def _embed(
        self, texts: tuple[str, ...], *, prefix: str, operation: str
    ) -> tuple[tuple[float, ...], ...]:
        if not texts or len(texts) > self._max_batch_size:
            raise EmbeddingError("BATCH_LIMIT_EXCEEDED")
        if any(not text.strip() for text in texts):
            raise EmbeddingError("EMPTY_EMBEDDING_INPUT")
        temperature = "warm" if self._warmed else "cold"
        started = time.perf_counter()
        future = self._executor.submit(self._backend.encode, tuple(prefix + text for text in texts))
        outcome = "success"
        try:
            raw = future.result(timeout=self._timeout_seconds)
            vectors = tuple(tuple(float(value) for value in vector) for vector in raw)
            if len(vectors) != len(texts) or any(not self._valid(vector) for vector in vectors):
                raise EmbeddingError("INVALID_VECTOR")
            self._warmed = True
            return vectors
        except TimeoutError as error:
            future.cancel()
            outcome = "timeout"
            raise EmbeddingError("EMBEDDING_TIMEOUT") from error
        except EmbeddingError:
            outcome = "invalid"
            raise
        except Exception as error:
            outcome = "backend_error"
            raise EmbeddingError("EMBEDDING_BACKEND_FAILED") from error
        finally:
            self._metrics.record(
                EmbeddingMetricSample(
                    operation=operation,
                    temperature=temperature,
                    profile_id=self.profile.profile_id,
                    batch_size=len(texts),
                    latency_seconds=time.perf_counter() - started,
                    rss_bytes=_max_rss_bytes(),
                    outcome=outcome,
                )
            )

    def _valid(self, vector: tuple[float, ...]) -> bool:
        if len(vector) != self.profile.dimensions or not all(map(math.isfinite, vector)):
            return False
        norm = math.sqrt(sum(value * value for value in vector))
        return abs(norm - 1.0) <= self.profile.normalization_tolerance


def _max_rss_bytes() -> int:
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(rss if sys.platform == "darwin" else rss * 1024)
