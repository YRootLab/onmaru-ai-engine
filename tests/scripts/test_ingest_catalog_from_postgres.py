from __future__ import annotations

import pytest

from onmaru_ai.corpus import embedding_selection
from onmaru_ai.corpus.embedding_selection import select_embedding_backend
from onmaru_ai.embedding import (
    DETERMINISTIC_HASH_384,
    E5_SMALL_ONNX_INT8_384,
    DeterministicHashBackend,
)
from scripts.ingest_catalog_from_postgres import (
    _failure_count,
    _record_failure,
    _remove_failure,
    resolve_region_code,
)


@pytest.mark.parametrize(
    ("incoming", "expected"),
    [("kr-datalab-47130", "KR-47"), ("kr-datalab-51150", "KR-42")],
)
def test_ingestion_normalizes_dynamic_catalog_region_ids(incoming: str, expected: str) -> None:
    assert resolve_region_code(incoming, "") == expected


def test_ingestion_requires_local_model_for_real_embedding() -> None:
    with pytest.raises(ValueError, match="ONMARU_E5_ONNX_DIR"):
        select_embedding_backend(model_dir="", hash_only=False, dry_run=False)


def test_ingestion_selects_local_e5_backend(monkeypatch: pytest.MonkeyPatch) -> None:
    class Backend:
        model_id = E5_SMALL_ONNX_INT8_384.model_id
        model_commit = E5_SMALL_ONNX_INT8_384.model_commit
        dimensions = 384

        def __init__(self, model_dir: str) -> None:
            self.model_dir = model_dir

    monkeypatch.setattr(embedding_selection, "OnnxE5EmbeddingBackend", Backend)
    backend, profile = select_embedding_backend(
        model_dir="/models/e5", hash_only=False, dry_run=False
    )

    assert isinstance(backend, Backend)
    assert backend.model_dir == "/models/e5"
    assert profile == E5_SMALL_ONNX_INT8_384


def test_hash_mode_is_local_only_and_dry_run_only() -> None:
    backend, profile = select_embedding_backend(model_dir="", hash_only=True, dry_run=True)

    assert isinstance(backend, DeterministicHashBackend)
    assert profile == DETERMINISTIC_HASH_384
    with pytest.raises(ValueError, match="requires --dry-run"):
        select_embedding_backend(model_dir="", hash_only=True, dry_run=False)


def test_failure_manifest_records_and_clears_only_retried_places(tmp_path) -> None:
    manifest = tmp_path / "failed.jsonl"
    _record_failure(manifest, "place-1", RuntimeError("transient"))
    _record_failure(manifest, "place-2", ValueError("bad input"))
    assert _failure_count(manifest) == 2

    _remove_failure(manifest, "place-1")
    assert _failure_count(manifest) == 1
    assert '"place_id": "place-2"' in manifest.read_text(encoding="utf-8")

    _remove_failure(manifest, "place-2")
    assert not manifest.exists()
