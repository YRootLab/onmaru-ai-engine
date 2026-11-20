from __future__ import annotations

import json
from hashlib import sha256

import pytest

from onmaru_ai.embedding import E5_SMALL_384, E5_SMALL_ONNX_INT8_384, EmbeddingError
from onmaru_ai.embedding.onnx_backend import OnnxE5EmbeddingBackend


def _digest(value: bytes) -> str:
    return sha256(value).hexdigest()


def test_onnx_backend_rejects_incomplete_artifact(tmp_path) -> None:
    with pytest.raises(EmbeddingError, match="E5_ONNX_ARTIFACT_INCOMPLETE"):
        OnnxE5EmbeddingBackend(tmp_path)


def test_onnx_backend_rejects_artifact_for_different_profile(tmp_path) -> None:
    model = b"onnx model placeholder"
    tokenizer = b"tokenizer placeholder"
    tokenizer_json = b"{}"
    token_id_map = b"\x00\x00\x00\x00"
    (tmp_path / "model.onnx").write_bytes(model)
    (tmp_path / "sentencepiece.bpe.model").write_bytes(tokenizer)
    (tmp_path / "tokenizer.json").write_bytes(tokenizer_json)
    (tmp_path / "token-id-map.bin").write_bytes(token_id_map)
    (tmp_path / "onmaru-e5-manifest.json").write_text(
        json.dumps(
            {
                "model_id": E5_SMALL_384.model_id,
                "model_commit": E5_SMALL_384.model_commit,
                "profile_id": "wrong-profile",
                "dimensions": 384,
                "quantization": "dynamic-int8",
                "token_vocab_size": 1,
                "pad_token_id": 1,
                "model_sha256": _digest(model),
                "tokenizer_sha256": _digest(tokenizer),
                "tokenizer_json_sha256": _digest(tokenizer_json),
                "token_id_map_sha256": _digest(token_id_map),
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(EmbeddingError, match="E5_ONNX_ARTIFACT_MISMATCH"):
        OnnxE5EmbeddingBackend(tmp_path)


def test_onnx_profile_is_distinct_from_unquantized_e5() -> None:
    assert E5_SMALL_ONNX_INT8_384.profile_id != E5_SMALL_384.profile_id
    assert E5_SMALL_ONNX_INT8_384.query_prefix == E5_SMALL_384.query_prefix
    assert E5_SMALL_ONNX_INT8_384.passage_prefix == E5_SMALL_384.passage_prefix
