from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from onmaru_ai.corpus.staging_spool import CorpusStagingSpool
from onmaru_ai.storage.models import Chunk, Document, Embedding, Revision, text_hash


def _bundle(
    revision_id: str = "rev-spool",
) -> tuple[Revision, tuple[Document, ...], tuple[Chunk, ...], tuple[Embedding, ...]]:
    document = Document(
        document_id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        place_id=UUID("123e4567-e89b-12d3-a456-426614174001"),
        source_type="TOUR_API",
        source_id="public-1",
        source_revision="source-r1",
        title="한옥",
        published_at=datetime(2026, 1, 1, tzinfo=UTC),
        collected_at=datetime(2026, 1, 1, tzinfo=UTC),
        license_code="KOGL-1",
        region_code="KR-11",
        category_code="HANOK",
        normalized_text="한옥 장소",
        content_hash=text_hash("한옥 장소"),
    )
    chunk = Chunk(
        chunk_id=UUID("123e4567-e89b-12d3-a456-426614174002"),
        document_id=document.document_id,
        ordinal=0,
        start_offset=0,
        end_offset=5,
        chunk_text="한옥 장소",
        content_hash=text_hash("한옥 장소"),
        search_text="한옥 장소",
    )
    embedding = Embedding(chunk.chunk_id, "profile-e5", (1.0,) + (0.0,) * 383)
    revision = Revision(
        revision_id=revision_id,
        source_revision="export-r1",
        embedding_profile_id="profile-e5",
        chunker_version="chunker-v1",
        dictionary_version="dictionary-v1",
        config_hash="sha256:" + "a" * 64,
        document_hashes=((document.document_id, document.digest()),),
        chunk_count=1,
        embedding_count=1,
    )
    return revision, (document,), (chunk,), (embedding,)


def test_staging_spool_persists_place_checkpoint_and_original_timestamp(tmp_path) -> None:
    revision, documents, chunks, embeddings = _bundle()
    path = tmp_path / "stage.sqlite"
    expected_timestamp = datetime(2026, 11, 20, 0, 0, tzinfo=UTC)
    with CorpusStagingSpool(
        path, revision.revision_id, run_timestamp=expected_timestamp
    ) as spool:
        assert spool.run_timestamp == expected_timestamp
        spool.append("public-1", revision, documents, chunks, embeddings)
        assert spool.has_place("public-1")
        assert spool.counts() == (1, 1, 1)
    with CorpusStagingSpool(path, revision.revision_id) as resumed:
        assert resumed.run_timestamp == expected_timestamp
        assert resumed.has_place("public-1")
        assert resumed.revision().manifest_hash == revision.manifest_hash
        assert tuple(resumed.documents()) == documents
        assert tuple(resumed.chunks()) == chunks
        assert tuple(resumed.embeddings()) == embeddings
