"""Offline CPU inference for the pinned multilingual E5 ONNX artifact."""

from __future__ import annotations

import hashlib
import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

from onmaru_ai.embedding.service import E5_SMALL_ONNX_INT8_384, EmbeddingError


class OnnxE5EmbeddingBackend:
    """Run a pinned, dynamically quantized E5 ONNX model without network access."""

    model_id = E5_SMALL_ONNX_INT8_384.model_id
    model_commit = E5_SMALL_ONNX_INT8_384.model_commit
    dimensions = E5_SMALL_ONNX_INT8_384.dimensions

    def __init__(self, model_dir: str | Path, *, intra_op_threads: int = 1) -> None:
        root = Path(model_dir)
        manifest_path = root / "onmaru-e5-manifest.json"
        model_path = root / "model.onnx"
        tokenizer_path = root / "sentencepiece.bpe.model"
        tokenizer_json_path = root / "tokenizer.json"
        token_id_map_path = root / "token-id-map.bin"
        if (
            not manifest_path.is_file()
            or not model_path.is_file()
            or not tokenizer_path.is_file()
            or not tokenizer_json_path.is_file()
            or not token_id_map_path.is_file()
        ):
            raise EmbeddingError("E5_ONNX_ARTIFACT_INCOMPLETE")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if (
                manifest["model_id"] != self.model_id
                or manifest["model_commit"] != E5_SMALL_ONNX_INT8_384.model_commit.split(":")[0]
                or manifest["dimensions"] != self.dimensions
                or manifest["profile_id"] != E5_SMALL_ONNX_INT8_384.profile_id
                or manifest["quantization"] != "dynamic-int8"
                or manifest["token_vocab_size"] <= 0
                or manifest["model_sha256"] != _sha256(model_path)
                or manifest["tokenizer_sha256"] != _sha256(tokenizer_path)
                or manifest["tokenizer_json_sha256"] != _sha256(tokenizer_json_path)
                or manifest["token_id_map_sha256"] != _sha256(token_id_map_path)
            ):
                raise EmbeddingError("E5_ONNX_ARTIFACT_MISMATCH")

            import numpy as np
            import onnxruntime as ort  # type: ignore[import-untyped]

            self._token_id_map: Any = None
            options = ort.SessionOptions()
            options.intra_op_num_threads = max(1, intra_op_threads)
            options.inter_op_num_threads = 1
            options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
            self._session = ort.InferenceSession(
                str(model_path), sess_options=options, providers=["CPUExecutionProvider"]
            )
            try:
                import sentencepiece as spm  # type: ignore[import-not-found]

                self._tokenizer = spm.SentencePieceProcessor(model_file=str(tokenizer_path))
                self._token_id_map = np.fromfile(token_id_map_path, dtype="<i4")
                if len(self._token_id_map) != manifest["token_vocab_size"]:
                    raise EmbeddingError("E5_ONNX_TOKENIZER_CONTRACT_MISMATCH")
                self._pad_token_id = int(manifest["pad_token_id"])
                self._tokenizer_kind = "sentencepiece"
            except ImportError:
                from tokenizers import Tokenizer  # type: ignore[import-untyped]

                self._tokenizer = Tokenizer.from_file(str(tokenizer_json_path))
                fast_pad_id = self._tokenizer.token_to_id("<pad>")
                if fast_pad_id is None:
                    raise EmbeddingError("E5_ONNX_TOKENIZER_CONTRACT_MISMATCH") from None
                self._token_id_map = None
                self._pad_token_id = fast_pad_id
                self._tokenizer_kind = "tokenizers"
            self._np = np
            self._inputs = {entry.name for entry in self._session.get_inputs()}
            self._output = self._session.get_outputs()[0].name
        except EmbeddingError:
            raise
        except Exception as error:
            raise EmbeddingError("E5_ONNX_ARTIFACT_LOAD_FAILED") from error
        if not {"input_ids", "attention_mask"}.issubset(self._inputs):
            raise EmbeddingError("E5_ONNX_INPUT_CONTRACT_MISMATCH")

    def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        if not texts:
            return ()
        try:
            if self._tokenizer_kind == "sentencepiece":
                tokenized = [
                    [
                        self._mapped_token_id(self._tokenizer.bos_id()),
                        *(
                            self._mapped_token_id(token_id)
                            for token_id in self._tokenizer.encode(text)[:510]
                        ),
                        self._mapped_token_id(self._tokenizer.eos_id()),
                    ]
                    for text in texts
                ]
            else:
                tokenized = [
                    item.ids[:512]
                    for item in self._tokenizer.encode_batch(list(texts), add_special_tokens=True)
                ]
            if self._pad_token_id is None:
                raise EmbeddingError("E5_ONNX_TOKENIZER_CONTRACT_MISMATCH")
            max_length = max(len(ids) for ids in tokenized)
            input_ids = [ids + [self._pad_token_id] * (max_length - len(ids)) for ids in tokenized]
            attention = [[1] * len(ids) + [0] * (max_length - len(ids)) for ids in tokenized]
            feed: dict[str, Any] = {
                "input_ids": self._np.asarray(input_ids, dtype=self._np.int64),
                "attention_mask": self._np.asarray(attention, dtype=self._np.int64),
            }
            if "token_type_ids" in self._inputs:
                feed["token_type_ids"] = self._np.zeros_like(feed["input_ids"])
            hidden = self._session.run([self._output], feed)[0]
            mask = feed["attention_mask"][..., None].astype(hidden.dtype)
            pooled = (hidden * mask).sum(axis=1) / self._np.maximum(mask.sum(axis=1), 1e-9)
            norms = self._np.linalg.norm(pooled, axis=1, keepdims=True)
            if self._np.any(norms <= 0):
                raise EmbeddingError("E5_ONNX_ZERO_NORM")
            normalized = pooled / norms
            if normalized.shape != (len(texts), self.dimensions):
                raise EmbeddingError("E5_ONNX_OUTPUT_DIM_MISMATCH")
            vectors = tuple(tuple(float(value) for value in row) for row in normalized)
            if any(not math.isfinite(value) for vector in vectors for value in vector):
                raise EmbeddingError("E5_ONNX_INVALID_VECTOR")
            return vectors
        except EmbeddingError:
            raise
        except Exception as error:
            raise EmbeddingError("E5_ONNX_INFERENCE_FAILED") from error

    def _mapped_token_id(self, token_id: int) -> int:
        if token_id < 0 or token_id >= len(self._token_id_map):
            raise EmbeddingError("E5_ONNX_TOKENIZER_CONTRACT_MISMATCH")
        return int(self._token_id_map[token_id])


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@lru_cache(maxsize=2)
def load_e5_backend(model_dir: str) -> OnnxE5EmbeddingBackend:
    return OnnxE5EmbeddingBackend(model_dir)
