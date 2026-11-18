-- PostgreSQL 17. Run as the AI migration owner.
-- Only editorially reviewed spans can authorize generated claims.

CREATE TABLE ai.reviewed_facts (
    revision_id text NOT NULL,
    fact_id text NOT NULL CHECK (btrim(fact_id) <> ''),
    chunk_id uuid NOT NULL,
    place_id text NOT NULL CHECK (btrim(place_id) <> ''),
    start_offset integer NOT NULL CHECK (start_offset >= 0),
    end_offset integer NOT NULL CHECK (end_offset > start_offset),
    fact_text text NOT NULL CHECK (btrim(fact_text) <> '' AND length(fact_text) <= 1000),
    kind text NOT NULL CHECK (kind IN ('FACT', 'INTERPRETATION', 'PREFERENCE')),
    support_type text NOT NULL CHECK (support_type IN (
        'CANONICAL_VALUE', 'HISTORICAL_FACT', 'VERIFIED_RELATION',
        'CONDITIONAL_PREFERENCE', 'INTERPRETATION'
    )),
    time_scope text NOT NULL CHECK (btrim(time_scope) <> '' AND length(time_scope) <= 100),
    relation jsonb,
    review_status text NOT NULL DEFAULT 'DRAFT' CHECK (review_status IN ('DRAFT', 'APPROVED', 'REVOKED')),
    approved_by text,
    approved_at timestamptz,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (revision_id, fact_id),
    FOREIGN KEY (revision_id, chunk_id) REFERENCES ai.chunks (revision_id, chunk_id),
    CHECK ((support_type = 'VERIFIED_RELATION') = (relation IS NOT NULL)),
    CHECK ((review_status = 'APPROVED') = (approved_by IS NOT NULL AND approved_at IS NOT NULL))
);

CREATE INDEX reviewed_facts_active_chunk
    ON ai.reviewed_facts (revision_id, chunk_id, fact_id)
    WHERE review_status = 'APPROVED';

REVOKE ALL ON ai.reviewed_facts FROM PUBLIC;
