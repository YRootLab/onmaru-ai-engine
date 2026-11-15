from __future__ import annotations

import json
import math

import httpx
import pytest

from onmaru_ai.embedding import (
    GEMINI_EMBEDDING_384,
    EmbeddingError,
    EmbeddingService,
    GeminiEmbeddingBackend,
)


def test_gemini_embedding_backend_normalizes_and_batches() -> None:
    captured: list[dict[str, object]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        captured.append(body)
        reqs = body["requests"]
        # Return unnormalized 384-d vectors (norm != 1.0) like raw truncated Matryoshka outputs
        embs = [{"values": [0.02] * 384} for _ in reqs]
        return httpx.Response(200, json={"embeddings": embs})

    transport = httpx.MockTransport(handler)
    backend = GeminiEmbeddingBackend(
        "test-api-key",
        task_type="RETRIEVAL_DOCUMENT",
        transport=transport,
    )
    service = EmbeddingService(backend, profile=GEMINI_EMBEDDING_384, max_batch_size=4)
    vecs = service.embed_passages(("경주 불국사", "서울 북촌 한옥마을"))

    assert len(vecs) == 2
    assert len(captured) == 1
    assert captured[0]["requests"][0]["outputDimensionality"] == 384  # type: ignore[index]
    assert captured[0]["requests"][0]["taskType"] == "RETRIEVAL_DOCUMENT"  # type: ignore[index]
    for vec in vecs:
        assert len(vec) == 384
        assert abs(math.sqrt(sum(v * v for v in vec)) - 1.0) < 1e-6


def test_gemini_embedding_backend_validation_errors() -> None:
    with pytest.raises(ValueError, match="api_key"):
        GeminiEmbeddingBackend("   ")

    def bad_count(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": []})

    backend = GeminiEmbeddingBackend("k", transport=httpx.MockTransport(bad_count))
    with pytest.raises(EmbeddingError, match="GEMINI_EMBEDDING_COUNT_MISMATCH"):
        backend.encode(("hello",))

    def bad_dim(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"embeddings": [{"values": [1.0, 2.0]}]})

    backend_dim = GeminiEmbeddingBackend("k", transport=httpx.MockTransport(bad_dim))
    with pytest.raises(EmbeddingError, match="GEMINI_EMBEDDING_DIM_MISMATCH"):
        backend_dim.encode(("hello",))
