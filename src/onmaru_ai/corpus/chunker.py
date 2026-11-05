"""Paragraph-first chunking for W1-approved public source projections."""

from __future__ import annotations

import hashlib
import re
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from .normalizer import NormalizedSourceText, SourceTextNormalizer
from .source_policy import PublicSourceProjection, SourcePolicy

_NON_SPACE = re.compile(r"\S+")


@dataclass(frozen=True)
class ChunkingDocument:
    revision_id: str
    source: PublicSourceProjection
    body: str
    collected_at: datetime
    region: str
    category: str


@dataclass(frozen=True)
class SourceChunk:
    revision_id: str
    document_id: str
    chunk_id: str
    ordinal: int
    place_id: str
    source_type: str
    source_id: str
    source_revision: str
    published_at: datetime
    collected_at: datetime
    license: str
    region: str
    category: str
    content_hash: str
    chunker_version: str
    start_offset: int
    end_offset: int
    token_count: int
    text: str
    content_type: str = "UNTRUSTED_SOURCE_TEXT"


@dataclass(frozen=True)
class _Token:
    text: str
    start: int
    end: int


class SemanticChunker:
    """Keep meaningful paragraphs when possible, splitting only at the hard bound.

    Token counts use a deterministic whitespace profile. The profile is versioned by
    ``chunker_version`` so a future model tokenizer change necessarily creates new IDs.
    """

    def __init__(
        self,
        *,
        target_tokens: int = 400,
        max_tokens: int = 600,
        overlap_tokens: int = 60,
        chunker_version: str = "semantic-whitespace-v1",
        normalizer: SourceTextNormalizer | None = None,
    ) -> None:
        if target_tokens <= 0 or max_tokens <= 0 or target_tokens > max_tokens:
            raise ValueError("invalid chunk sizes")
        if overlap_tokens < 0 or overlap_tokens >= target_tokens:
            raise ValueError("invalid overlap")
        if not chunker_version.strip():
            raise ValueError("chunker_version must not be blank")
        self._target = target_tokens
        self._maximum = max_tokens
        self._overlap = overlap_tokens
        self._version = chunker_version
        self._normalizer = normalizer or SourceTextNormalizer()

    def split_many(self, documents: Iterable[ChunkingDocument]) -> tuple[SourceChunk, ...]:
        # Each document is normalized and split independently. This is the boundary that
        # prevents place/source/revision content from being coalesced.
        return tuple(chunk for document in documents for chunk in self.split(document))

    def split(self, document: ChunkingDocument) -> tuple[SourceChunk, ...]:
        if not SourcePolicy.permits(document.source):
            raise ValueError("SOURCE_NOT_ELIGIBLE")
        invalid_revision = not document.revision_id or any(
            character.isspace() for character in document.revision_id
        )
        if invalid_revision:
            raise ValueError("REVISION_ID_INVALID")
        if document.collected_at.tzinfo is None or document.collected_at.utcoffset() is None:
            raise ValueError("COLLECTED_AT_MUST_BE_AWARE")
        if not document.region.strip() or not document.category.strip():
            raise ValueError("SOURCE_METADATA_INCOMPLETE")
        normalized = self._normalizer.normalize(document.body)
        tokens = tuple(
            _Token(match.group(), match.start(), match.end())
            for match in _NON_SPACE.finditer(normalized.text)
        )
        if not tokens:
            raise ValueError("DOCUMENT_TEXT_EMPTY")

        ranges = self._ranges(tokens, normalized)
        return tuple(
            self._make_chunk(document, normalized, tokens, ordinal, start, end)
            for ordinal, (start, end) in enumerate(ranges)
        )

    def _ranges(
        self, tokens: tuple[_Token, ...], normalized: NormalizedSourceText
    ) -> tuple[tuple[int, int], ...]:
        paragraphs: list[tuple[int, int]] = []
        paragraph_start = 0
        for index in range(1, len(tokens)):
            if "\n" in normalized.text[tokens[index - 1].end : tokens[index].start]:
                paragraphs.append((paragraph_start, index))
                paragraph_start = index
        paragraphs.append((paragraph_start, len(tokens)))

        ranges: list[tuple[int, int]] = []
        pending_start: int | None = None
        pending_end = 0
        for start, end in paragraphs:
            count = end - start
            if count > self._maximum:
                if pending_start is not None:
                    ranges.append((pending_start, pending_end))
                    pending_start = None
                ranges.extend(self._split_oversized(start, end))
            elif pending_start is None:
                pending_start, pending_end = start, end
            elif end - pending_start <= self._target:
                pending_end = end
            else:
                ranges.append((pending_start, pending_end))
                pending_start, pending_end = start, end
        if pending_start is not None:
            ranges.append((pending_start, pending_end))
        return tuple(ranges)

    def _split_oversized(self, start: int, end: int) -> list[tuple[int, int]]:
        ranges: list[tuple[int, int]] = []
        cursor = start
        while cursor < end:
            chunk_end = min(cursor + self._target, end)
            ranges.append((cursor, chunk_end))
            if chunk_end == end:
                break
            cursor = chunk_end - self._overlap
        return ranges

    def _make_chunk(
        self,
        document: ChunkingDocument,
        normalized: NormalizedSourceText,
        tokens: tuple[_Token, ...],
        ordinal: int,
        start: int,
        end: int,
    ) -> SourceChunk:
        normalized_start = tokens[start].start
        normalized_end = tokens[end - 1].end
        text = normalized.text[normalized_start:normalized_end]
        source_start, source_end = normalized.source_range(normalized_start, normalized_end)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        source = document.source
        assert source.license_code is not None  # SourcePolicy.permits guarantees this.
        return SourceChunk(
            revision_id=document.revision_id,
            document_id=source.document_id,
            chunk_id=f"{source.document_id}:{self._version}:{ordinal}:{digest}",
            ordinal=ordinal,
            place_id=source.place_id,
            source_type=source.source_type,
            source_id=source.source_id,
            source_revision=source.source_revision,
            published_at=source.published_at,
            collected_at=document.collected_at,
            license=source.license_code,
            region=document.region,
            category=document.category,
            content_hash=f"sha256:{digest}",
            chunker_version=self._version,
            start_offset=source_start,
            end_offset=source_end,
            token_count=end - start,
            text=text,
        )
