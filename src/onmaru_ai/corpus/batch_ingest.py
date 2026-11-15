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
from onmaru_ai.corpus.normalizer import SourceTextNormalizer
from onmaru_ai.corpus.source_policy import PublicSourceProjection
from onmaru_ai.embedding import E5_SMALL_384, EmbeddingService
from onmaru_ai.storage.models import Chunk, Document, Embedding, Revision, text_hash

logger = logging.getLogger(__name__)


def _normalize_idempotent(normalizer: SourceTextNormalizer, body: str) -> str:
    current = normalizer.normalize(body).text
    for _ in range(3):
        nxt = normalizer.normalize(current).text
        if nxt == current:
            return current
        current = nxt
    return current


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
    *,
    embed_batch_size: int = 32,
) -> tuple[IngestResult, Revision, tuple[Document, ...], tuple[Chunk, ...], tuple[Embedding, ...]]:
    """Filters items by 12 approved categories, chunks, embeds, and produces a storage bundle."""
    current_time = now or datetime.now(UTC)
    normalizer = SourceTextNormalizer()
    chunker = SemanticChunker(normalizer=normalizer)

    docs: list[Document] = []
    chunks: list[Chunk] = []
    embeddings: list[Embedding] = []

    accepted_count = 0
    filtered_count = 0

    for item in items:
        if not is_approved_category(item.category_code):
            filtered_count += 1
            continue

        clean_body = _normalize_idempotent(normalizer, item.body).strip()
        if not clean_body:
            clean_body = _normalize_idempotent(normalizer, item.title).strip()
        if not clean_body:
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
            normalized_text=clean_body,
            content_hash=text_hash(clean_body),
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
            body=clean_body,
            collected_at=current_time,
            region=item.region_code,
            category=clean_cat,
        )

        produced_chunks = list(chunker.split(chunking_doc))
        for p_chunk in produced_chunks:
            chunk_uuid = uuid5(NAMESPACE_DNS, f"chunk:{p_chunk.chunk_id}")
            chunk_slice = clean_body[p_chunk.start_offset : p_chunk.end_offset]
            c_record = Chunk(
                chunk_id=chunk_uuid,
                document_id=doc_uuid,
                ordinal=p_chunk.ordinal,
                start_offset=p_chunk.start_offset,
                end_offset=p_chunk.end_offset,
                chunk_text=chunk_slice,
                content_hash=p_chunk.content_hash,
                search_text=f"{item.title} {item.region_code} {clean_cat} {chunk_slice}",
            )
            chunks.append(c_record)

    if embedding_service is not None and chunks:
        batch_len = max(1, embed_batch_size)
        for start in range(0, len(chunks), batch_len):
            batch_chunks = chunks[start : start + batch_len]
            vecs = embedding_service.embed_passages(
                tuple(chunk.search_text for chunk in batch_chunks)
            )
            for chunk, vec in zip(batch_chunks, vecs, strict=True):
                embeddings.append(
                    Embedding(
                        chunk_id=chunk.chunk_id,
                        embedding_profile_id=embedding_service.profile.profile_id,
                        values=vec,
                    )
                )

    profile_id = (
        embedding_service.profile.profile_id
        if embedding_service is not None
        else E5_SMALL_384.profile_id
    )
    rev_record = Revision(
        revision_id=revision_id,
        source_revision=f"export-{revision_id}",
        embedding_profile_id=profile_id,
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
