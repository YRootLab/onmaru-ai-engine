"""Strict input contract for editorially approved corpus facts."""

from __future__ import annotations

import html
import re
import unicodedata
from datetime import datetime
from typing import Literal, Self
from uuid import UUID

from psycopg.types.json import Jsonb
from pydantic import Field, ValidationError, field_validator, model_validator

from onmaru_ai.contracts.models import ClosedModel, Identifier
from onmaru_ai.contracts.vocabulary import ClaimKind
from onmaru_ai.generation.models import VerifiedRelation
from onmaru_ai.proposal.text_safety import is_safe_proposal_text


class ReviewedFactImport(ClosedModel):
    revision_id: Identifier
    fact_id: Identifier
    chunk_id: UUID
    place_id: Identifier
    start_offset: int = Field(ge=0, strict=True)
    end_offset: int = Field(gt=0, strict=True)
    fact_text: str = Field(min_length=1, max_length=1000)
    kind: ClaimKind
    support_type: Literal[
        "CANONICAL_VALUE",
        "HISTORICAL_FACT",
        "VERIFIED_RELATION",
        "CONDITIONAL_PREFERENCE",
        "INTERPRETATION",
    ]
    time_scope: str = Field(min_length=1, max_length=100)
    relation: VerifiedRelation | None
    review_status: Literal["APPROVED"]
    approved_by: Identifier
    approved_at: datetime

    @field_validator("approved_at")
    @classmethod
    def approval_timestamp_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("approvedAt must include a timezone")
        return value

    @model_validator(mode="after")
    def validate_approved_fact(self) -> Self:
        normalized = unicodedata.normalize("NFKC", self.fact_text)
        if (
            self.fact_text != self.fact_text.strip()
            or html.unescape(normalized) != normalized
            or not is_safe_proposal_text(normalized)
            or any(unicodedata.category(char).startswith("C") for char in self.fact_text)
            or re.search(r"[.!?。！？]\s*\D", normalized) is not None
        ):
            raise ValueError("factText is not a safe atomic claim")
        if (
            self.time_scope != self.time_scope.strip()
            or not is_safe_proposal_text(self.time_scope)
        ):
            raise ValueError("timeScope must be safe and trimmed")
        if self.end_offset <= self.start_offset:
            raise ValueError("endOffset must be greater than startOffset")
        if (self.support_type == "VERIFIED_RELATION") != (self.relation is not None):
            raise ValueError("relation is required only for VERIFIED_RELATION")
        if (self.kind == ClaimKind.PREFERENCE) != (
            self.support_type == "CONDITIONAL_PREFERENCE"
        ):
            raise ValueError("PREFERENCE facts require CONDITIONAL_PREFERENCE support")
        if (self.kind == ClaimKind.INTERPRETATION) != (self.support_type == "INTERPRETATION"):
            raise ValueError("INTERPRETATION facts require INTERPRETATION support")
        if self.kind == ClaimKind.CONNECTOR:
            raise ValueError("CONNECTOR facts cannot be imported")
        if self.time_scope != "TIMELESS" and self.time_scope not in self.fact_text:
            raise ValueError("timeScope must appear in factText")
        if self.relation is not None and self.place_id not in {
            self.relation.subject_id,
            self.relation.object_id,
        }:
            raise ValueError("relation must include the fact place")
        return self


def parse_reviewed_facts_jsonl(content: str) -> tuple[ReviewedFactImport, ...]:
    facts: list[ReviewedFactImport] = []
    seen: set[tuple[str, str]] = set()
    for line_number, raw_line in enumerate(content.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            fact = ReviewedFactImport.model_validate_json(raw_line)
        except ValidationError as exc:
            raise ValueError(f"invalid reviewed fact on line {line_number}") from exc
        key = (fact.revision_id, fact.fact_id)
        if key in seen:
            raise ValueError(f"duplicate reviewed fact ID on line {line_number}")
        seen.add(key)
        facts.append(fact)
    if not facts:
        raise ValueError("reviewed fact input is empty")
    return tuple(facts)


def validate_and_import_reviewed_facts(
    connection: object,
    facts: tuple[ReviewedFactImport, ...],
    *,
    apply: bool,
) -> int:
    """Validate all rows against the active corpus, then optionally insert atomically.

    The caller owns a PostgreSQL transaction and must roll it back if this function raises.
    """
    if not facts:
        raise ValueError("reviewed fact input is empty")
    revisions = {fact.revision_id for fact in facts}
    if len(revisions) != 1:
        raise ValueError("all reviewed facts must target one corpus revision")

    validation_query = """WITH inputs AS (
               SELECT * FROM unnest(%s::text[], %s::text[], %s::uuid[], %s::text[])
                 AS i(revision_id, fact_id, chunk_id, place_id)
           )
           SELECT i.revision_id, i.fact_id, a.revision_id AS active_revision,
                  c.start_offset AS chunk_start_offset, c.end_offset AS chunk_end_offset,
                  c.chunk_text, d.source_id, d.eligibility_status, d.normalized_text,
                  EXISTS (SELECT 1 FROM ai.place_revocations p
                           WHERE p.place_id=d.place_id) AS place_revoked,
                  EXISTS (SELECT 1 FROM ai.source_revocations s
                           WHERE (s.source_type,s.source_id,s.source_revision)=
                                 (d.source_type,d.source_id,d.source_revision)) AS source_revoked
             FROM inputs i
             JOIN ai.active_corpus a ON a.id=1
             LEFT JOIN ai.chunks c
               ON c.revision_id=i.revision_id AND c.chunk_id=i.chunk_id
             LEFT JOIN ai.documents d
               ON d.revision_id=c.revision_id AND d.document_id=c.document_id
            """
    if apply:
        validation_query += " FOR SHARE OF a"
    cursor = connection.execute(  # type: ignore[attr-defined]
        validation_query,
        (
            [fact.revision_id for fact in facts],
            [fact.fact_id for fact in facts],
            [fact.chunk_id for fact in facts],
            [fact.place_id for fact in facts],
        ),
    )
    rows = cursor.fetchall()
    rows_by_fact = {str(row["fact_id"]): row for row in rows}
    if len(rows_by_fact) != len(facts):
        raise ValueError("corpus lookup did not resolve every reviewed fact")

    for fact in facts:
        row = rows_by_fact.get(fact.fact_id)
        if (
            row is None
            or row["active_revision"] != fact.revision_id
            or row["source_id"] != fact.place_id
            or row["eligibility_status"] != "PUBLIC"
            or row["place_revoked"]
            or row["source_revoked"]
            or fact.start_offset < row["chunk_start_offset"]
            or fact.end_offset > row["chunk_end_offset"]
            or row["normalized_text"][fact.start_offset : fact.end_offset] != fact.fact_text
            or row["chunk_text"]
            != row["normalized_text"][row["chunk_start_offset"] : row["chunk_end_offset"]]
        ):
            raise ValueError(f"reviewed fact does not match active public corpus: {fact.fact_id}")

    if apply:
        for fact in facts:
            connection.execute(  # type: ignore[attr-defined]
                """INSERT INTO ai.reviewed_facts (
                       revision_id, fact_id, chunk_id, place_id, start_offset, end_offset,
                       fact_text, kind, support_type, time_scope, relation, review_status,
                       approved_by, approved_at
                   ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'APPROVED', %s, %s)""",
                (
                    fact.revision_id,
                    fact.fact_id,
                    fact.chunk_id,
                    fact.place_id,
                    fact.start_offset,
                    fact.end_offset,
                    fact.fact_text,
                    fact.kind.value,
                    fact.support_type,
                    fact.time_scope,
                    (
                        Jsonb(fact.relation.model_dump(by_alias=True))
                        if fact.relation is not None
                        else None
                    ),
                    fact.approved_by,
                    fact.approved_at,
                ),
            )
    return len(facts)
