from __future__ import annotations

import pytest

from onmaru_ai.corpus.staging_spool import CorpusStagingSpool
from onmaru_ai.storage.postgres import CorpusStorageError, _validate_spool
from tests.corpus.test_staging_spool import _bundle


def test_streaming_spool_validation_checks_manifest_without_materializing_vectors(tmp_path) -> None:
    revision, documents, chunks, embeddings = _bundle()
    with CorpusStagingSpool(tmp_path / "valid.sqlite", revision.revision_id) as spool:
        spool.append("public-1", revision, documents, chunks, embeddings)
        assert _validate_spool(spool) == revision


def test_streaming_spool_validation_rejects_bad_chunk_offsets(tmp_path) -> None:
    revision, documents, chunks, embeddings = _bundle()
    invalid = chunks[0].__class__(**{**chunks[0].__dict__, "end_offset": 500})
    with CorpusStagingSpool(tmp_path / "invalid.sqlite", revision.revision_id) as spool:
        spool.append("public-1", revision, documents, (invalid,), embeddings)
        with pytest.raises(CorpusStorageError, match="CHUNK_HASH_OFFSET_OR_DUPLICATE"):
            _validate_spool(spool)
