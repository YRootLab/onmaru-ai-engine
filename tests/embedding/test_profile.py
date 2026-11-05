from __future__ import annotations

import time

import pytest

from onmaru_ai.embedding import (
    E5_SMALL_384,
    EmbeddingError,
    EmbeddingService,
    EmbeddingWorkGate,
    InMemoryEmbeddingMetrics,
)


class Backend:
    model_id = E5_SMALL_384.model_id
    model_commit = E5_SMALL_384.model_commit
    dimensions = 384

    def __init__(self) -> None:
        self.inputs: list[tuple[str, ...]] = []

    def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        self.inputs.append(texts)
        return tuple((1.0,) + (0.0,) * 383 for _ in texts)


def test_passage_and_query_use_pinned_prefixes_and_profile() -> None:
    backend = Backend()
    service = EmbeddingService(backend, profile=E5_SMALL_384)

    passages = service.embed_passages(("첫 청크", "둘째 청크"))
    query = service.embed_query("고즈넉한 한옥")

    assert backend.inputs == [
        ("passage: 첫 청크", "passage: 둘째 청크"),
        ("query: 고즈넉한 한옥",),
    ]
    assert len(passages) == 2
    assert len(query) == 384
    assert service.profile.profile_id.endswith("@614241f622f5")


@pytest.mark.parametrize("field", ["model_id", "model_commit", "dimensions"])
def test_backend_must_match_pinned_profile(field: str) -> None:
    backend = Backend()
    setattr(backend, field, "wrong" if field != "dimensions" else 16)

    with pytest.raises(EmbeddingError, match="PROFILE_MISMATCH"):
        EmbeddingService(backend, profile=E5_SMALL_384)


@pytest.mark.parametrize(
    "vector",
    [
        (1.0,) + (0.0,) * 382,
        (float("nan"),) + (0.0,) * 383,
        (2.0,) + (0.0,) * 383,
        (0.0,) * 384,
    ],
)
def test_invalid_dimension_finite_value_or_norm_fails_closed(vector: tuple[float, ...]) -> None:
    class InvalidBackend(Backend):
        def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
            return (vector,) * len(texts)

    service = EmbeddingService(InvalidBackend(), profile=E5_SMALL_384)
    with pytest.raises(EmbeddingError, match="INVALID_VECTOR"):
        service.embed_query("질문")


def test_passage_batch_has_hard_limit() -> None:
    service = EmbeddingService(Backend(), profile=E5_SMALL_384, max_batch_size=2)
    with pytest.raises(EmbeddingError, match="BATCH_LIMIT_EXCEEDED"):
        service.embed_passages(("a", "b", "c"))


def test_offline_batch_is_rejected_while_online_embedding_is_active() -> None:
    gate = EmbeddingWorkGate()
    service = EmbeddingService(Backend(), profile=E5_SMALL_384, work_gate=gate)

    with gate.online(), pytest.raises(EmbeddingError, match="BATCH_DEFERRED"):
        service.embed_passages(("청크",))


def test_online_embedding_fails_closed_while_batch_is_active() -> None:
    gate = EmbeddingWorkGate()
    service = EmbeddingService(Backend(), profile=E5_SMALL_384, work_gate=gate)

    with gate.batch(), pytest.raises(EmbeddingError, match="ONLINE_EMBEDDING_BUSY"):
        service.embed_query("질문")


def test_timeout_fails_closed() -> None:
    class SlowBackend(Backend):
        def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
            time.sleep(0.05)
            return super().encode(texts)

    service = EmbeddingService(SlowBackend(), profile=E5_SMALL_384, timeout_seconds=0.001)
    with pytest.raises(EmbeddingError, match="EMBEDDING_TIMEOUT"):
        service.embed_query("질문")


def test_cold_and_warm_latency_and_rss_are_recorded_without_text() -> None:
    metrics = InMemoryEmbeddingMetrics()
    service = EmbeddingService(Backend(), profile=E5_SMALL_384, metrics=metrics)
    service.embed_query("비밀 질문")
    service.embed_query("다른 질문")

    assert [sample.temperature for sample in metrics.samples] == ["cold", "warm"]
    assert all(sample.latency_seconds >= 0 for sample in metrics.samples)
    assert all(sample.rss_bytes > 0 for sample in metrics.samples)
    assert "비밀" not in repr(metrics.samples)
