#!/usr/bin/env python3
"""Export the pinned E5 model to a hashed, dynamically quantized ONNX artifact.

Run with ``uv run --group embedding-export python scripts/export_e5_onnx.py --output
<artifact-dir>``. This is an offline preparation command; serving never downloads models.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

from onmaru_ai.embedding import E5_SMALL_384, E5_SMALL_ONNX_INT8_384


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _build_token_id_map(
    tokenizer_json: Path, sentencepiece_model: Path, output: Path
) -> dict[str, int]:
    import numpy as np
    from sentencepiece import SentencePieceProcessor
    from tokenizers import Tokenizer

    fast_tokenizer = Tokenizer.from_file(str(tokenizer_json))
    sentencepiece = SentencePieceProcessor(model_file=str(sentencepiece_model))
    token_id_map: list[int] = []
    for token_id in range(sentencepiece.get_piece_size()):
        piece = sentencepiece.id_to_piece(token_id)
        mapped = fast_tokenizer.token_to_id(piece)
        if mapped is None:
            raise ValueError(f"SentencePiece token is absent from tokenizer.json: {piece!r}")
        token_id_map.append(mapped)
    samples = (
        "query: 고즈넉한 한옥과 전통 문화를 경험할 수 있는 여행지",
        "passage: 경상북도 경주시의 역사 유적과 관광 정보를 소개합니다.",
        "query: Jeju Island 2026 12345 café",
        "passage: " + "한옥 마을과 전통 문화를 소개하는 문장입니다. " * 80,
    )
    for text in samples:
        encoded = fast_tokenizer.encode(text, add_special_tokens=True).ids
        expected = [encoded[0], *encoded[1:-1][:510], encoded[-1]]
        raw = [sentencepiece.bos_id(), *sentencepiece.encode(text)[:510], sentencepiece.eos_id()]
        actual = [token_id_map[token_id] for token_id in raw]
        if expected != actual:
            raise ValueError("Mapped SentencePiece tokenization differs from pinned tokenizer.json")
    np.asarray(token_id_map, dtype="<i4").tofile(output / "token-id-map.bin")
    pad_id = fast_tokenizer.token_to_id("<pad>")
    if pad_id is None:
        raise ValueError("Pinned tokenizer has no <pad> token")
    return {"token_vocab_size": len(token_id_map), "pad_token_id": pad_id}


def export(output: Path) -> None:
    from huggingface_hub import hf_hub_download
    from onnxruntime.quantization import QuantType, quantize_dynamic
    from optimum.exporters.onnx import main_export

    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError("output directory must be empty")
    with tempfile.TemporaryDirectory(prefix="onmaru-e5-export-") as temporary:
        exported = Path(temporary) / "exported"
        main_export(
            E5_SMALL_384.model_id,
            output=exported,
            revision=E5_SMALL_384.model_commit,
            task="feature-extraction",
            opset=17,
        )
        source_model = exported / "model.onnx"
        if not source_model.is_file():
            raise FileNotFoundError("pinned export did not produce model.onnx")
        source_tokenizer = Path(
            hf_hub_download(
                repo_id=E5_SMALL_384.model_id,
                filename="sentencepiece.bpe.model",
                revision=E5_SMALL_384.model_commit,
            )
        )
        source_tokenizer_json = exported / "tokenizer.json"
        if not source_tokenizer_json.is_file():
            raise FileNotFoundError("pinned export did not produce tokenizer.json")
        tokenizer_metadata = _build_token_id_map(
            exported / "tokenizer.json", source_tokenizer, output
        )
        model_path = output / "model.onnx"
        quantize_dynamic(
            str(source_model),
            str(model_path),
            weight_type=QuantType.QInt8,
            per_channel=True,
        )
        tokenizer_path = output / "sentencepiece.bpe.model"
        shutil.copyfile(source_tokenizer, tokenizer_path)
        tokenizer_json_path = output / "tokenizer.json"
        shutil.copyfile(source_tokenizer_json, tokenizer_json_path)

    manifest = {
        "model_id": E5_SMALL_384.model_id,
        "model_commit": E5_SMALL_384.model_commit,
        "profile_id": E5_SMALL_ONNX_INT8_384.profile_id,
        "dimensions": E5_SMALL_384.dimensions,
        "quantization": "dynamic-int8",
        **tokenizer_metadata,
        "model_sha256": _sha256(model_path),
        "tokenizer_sha256": _sha256(tokenizer_path),
        "tokenizer_json_sha256": _sha256(tokenizer_json_path),
        "token_id_map_sha256": _sha256(output / "token-id-map.bin"),
    }
    (output / "onmaru-e5-manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        export(args.output)
    except (OSError, ValueError, RuntimeError) as error:
        print(f"E5 ONNX export failed: {error}", file=sys.stderr)
        return 1
    print(f"Pinned E5 ONNX artifact written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
