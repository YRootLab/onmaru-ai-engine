"""Batch pipeline for ingesting, chunking, and embedding approved category data."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import NAMESPACE_DNS, uuid5

from onmaru_ai.corpus.categories import is_approved_category
from onmaru_ai.corpus.chunker import (
    ChunkingDocument,
    SemanticChunker,
)
from onmaru_ai.corpus.source_policy import PublicSourceProjection
from onmaru_ai.embedding import E5_SMALL_384, EmbeddingService
from onmaru_ai.storage.models import Chunk, Document, Embedding, Revision, text_hash

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestItem:
    place_id: str
    title: str
    body: str
    region_code: str
    category_code: str
    source_type: str = "TOUR_API"
    source_id: str = "src-default"
    source_revision: str = "rev-0"
    license_code: str = "KOGL-1"


@dataclass(frozen=True)
class IngestResult:
    revision_id: str
    total_input: int
    accepted_documents: int
    filtered_out_categories: int
    total_chunks: int
    total_embeddings: int


def build_corpus_bundle(
    revision_id: str,
    items: list[IngestItem],
    embedding_service: EmbeddingService | None = None,
    now: datetime | None = None,
) -> tuple[IngestResult, Revision, tuple[Document, ...], tuple[Chunk, ...], tuple[Embedding, ...]]:
    """Filters items by 12 approved categories, chunks, embeds, and produces a storage bundle."""
    current_time = now or datetime.now(UTC)
    chunker = SemanticChunker()

    docs: list[Document] = []
    chunks: list[Chunk] = []
    embeddings: list[Embedding] = []

    accepted_count = 0
    filtered_count = 0

    for item in items:
        if not is_approved_category(item.category_code):
            filtered_count += 1
            continue

        clean_cat = item.category_code.strip().upper()
        doc_uuid = uuid5(NAMESPACE_DNS, f"{revision_id}:{item.place_id}:{item.source_id}")
        place_uuid = uuid5(NAMESPACE_DNS, f"place:{item.place_id}")

        doc_record = Document(
            document_id=doc_uuid,
            place_id=place_uuid,
            source_type=item.source_type,
            source_id=item.source_id,
            source_revision=item.source_revision,
            title=item.title,
            published_at=current_time,
            collected_at=current_time,
            license_code=item.license_code,
            region_code=item.region_code,
            category_code=clean_cat,
            normalized_text=item.body.strip(),
            content_hash=text_hash(item.body.strip()),
        )
        docs.append(doc_record)
        accepted_count += 1

        # Chunk the document
        fake_proj = PublicSourceProjection.model_validate(
            {
                "documentId": str(doc_uuid),
                "placeId": str(place_uuid),
                "sourceType": item.source_type,
                "sourceId": item.source_id,
                "sourceRevision": item.source_revision,
                "publishedAt": current_time,
                "documentHash": "sha256:" + "0" * 64,
                "contentUrl": f"https://catalog.onmaru.site/export/{item.place_id}",
                "licenseCode": item.license_code,
                "licenseVerified": True,
                "publicationEligible": True,
                "public": True,
                "revoked": False,
                "snapshotStatus": "OK",
                "reviewStatus": None,
            }
        )
        chunking_doc = ChunkingDocument(
            revision_id=revision_id,
            source=fake_proj,
            body=item.body,
            collected_at=current_time,
            region=item.region_code,
            category=clean_cat,
        )

        produced_chunks = list(chunker.split(chunking_doc))
        for p_chunk in produced_chunks:
            chunk_uuid = uuid5(NAMESPACE_DNS, f"chunk:{p_chunk.chunk_id}")
            c_record = Chunk(
                chunk_id=chunk_uuid,
                document_id=doc_uuid,
                ordinal=p_chunk.ordinal,
                start_offset=p_chunk.start_offset,
                end_offset=p_chunk.end_offset,
                chunk_text=item.body[p_chunk.start_offset:p_chunk.end_offset] or item.body[:200],
                content_hash=p_chunk.content_hash,
                search_text=item.title + " " + item.body[p_chunk.start_offset:p_chunk.end_offset],
            )
            chunks.append(c_record)

            if embedding_service is not None:
                vecs = embedding_service.embed_passages([c_record.search_text])
                emb_record = Embedding(
                    chunk_id=chunk_uuid,
                    embedding_profile_id=embedding_service.profile.profile_id,
                    values=vecs[0],
                )
                embeddings.append(emb_record)

    rev_record = Revision(
        revision_id=revision_id,
        source_revision=f"export-{revision_id}",
        embedding_profile_id=E5_SMALL_384.profile_id,
        chunker_version="paragraph-first-w1",
        dictionary_version="questions-1",
        config_hash="sha256:" + "c" * 64,
        document_hashes=tuple((d.document_id, d.digest()) for d in docs),
        chunk_count=len(chunks),
        embedding_count=len(embeddings),
    )

    result = IngestResult(
        revision_id=revision_id,
        total_input=len(items),
        accepted_documents=accepted_count,
        filtered_out_categories=filtered_count,
        total_chunks=len(chunks),
        total_embeddings=len(embeddings),
    )

    return result, rev_record, tuple(docs), tuple(chunks), tuple(embeddings)
