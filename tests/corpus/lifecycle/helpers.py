from datetime import UTC, datetime
from uuid import UUID

from onmaru_ai.storage.models import Chunk, Document, Embedding, Revision, text_hash
from onmaru_ai.storage.postgres import PostgresCorpusStore

DOCUMENT = UUID("00000000-0000-0000-0000-000000000001")
CHUNK = UUID("00000000-0000-0000-0000-000000000002")
PLACE = UUID("00000000-0000-0000-0000-000000000003")
NOW = datetime(2026, 11, 5, tzinfo=UTC)


def bundle(
    revision_id: str,
) -> tuple[Revision, tuple[Document, ...], tuple[Chunk, ...], tuple[Embedding, ...]]:
    document = Document(
        document_id=DOCUMENT,
        place_id=PLACE,
        source_type="TOUR",
        source_id="source-1",
        source_revision="source-v1",
        title="한옥",
        published_at=NOW,
        collected_at=NOW,
        license_code="PUBLIC",
        region_code="KR-11",
        category_code="HANOK",
        normalized_text="한옥 이야기",
        content_hash=text_hash("한옥 이야기"),
    )
    chunk = Chunk(
        chunk_id=CHUNK,
        document_id=DOCUMENT,
        ordinal=0,
        start_offset=0,
        end_offset=6,
        chunk_text="한옥 이야기",
        content_hash=text_hash("한옥 이야기"),
        search_text="한옥 이야기",
    )
    embedding = Embedding(
        chunk_id=CHUNK, embedding_profile_id="e5-small-384", values=(1.0,) + (0.0,) * 383
    )
    revision = Revision(
        revision_id=revision_id,
        source_revision="export-v1",
        embedding_profile_id="e5-small-384",
        chunker_version="paragraph-1",
        dictionary_version="questions-1",
        config_hash=text_hash(revision_id),
        document_hashes=((DOCUMENT, document.digest()),),
        chunk_count=1,
        embedding_count=1,
    )
    return revision, (document,), (chunk,), (embedding,)


def activate(store: PostgresCorpusStore, revision: Revision, previous: str | None) -> None:
    store.activate(
        revision.revision_id,
        manifest_hash=revision.manifest_hash,
        expected_active=previous,
        expected_revocation_sequence=0,
    )
