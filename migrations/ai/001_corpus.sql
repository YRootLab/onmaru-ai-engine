-- PostgreSQL 17. Run as the separately provisioned AI migration owner.
CREATE SCHEMA ai;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
REVOKE ALL ON SCHEMA ai FROM PUBLIC;

CREATE TABLE ai.corpus_revisions (
    revision_id text PRIMARY KEY CHECK (btrim(revision_id) <> ''),
    manifest_hash text NOT NULL UNIQUE,
    manifest jsonb NOT NULL,
    source_revision text NOT NULL,
    state text NOT NULL CHECK (state IN ('BUILDING','VALIDATED','ACTIVE','RETIRED','REJECTED')),
    embedding_profile_id text NOT NULL,
    chunker_version text NOT NULL,
    dictionary_version text NOT NULL,
    config_hash text NOT NULL,
    document_count bigint NOT NULL CHECK (document_count >= 0),
    chunk_count bigint NOT NULL CHECK (chunk_count >= 0),
    embedding_count bigint NOT NULL CHECK (embedding_count >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    activated_at timestamptz,
    retired_at timestamptz,
    gc_state text NOT NULL DEFAULT 'LIVE' CHECK (gc_state IN ('LIVE','PENDING','DELETING','DELETED')),
    expires_at timestamptz,
    UNIQUE (revision_id, embedding_profile_id)
);
CREATE UNIQUE INDEX one_active_revision ON ai.corpus_revisions ((state)) WHERE state = 'ACTIVE';
CREATE TABLE ai.revocation_state (
    id integer PRIMARY KEY CHECK (id = 1),
    sequence bigint NOT NULL CHECK (sequence >= 0),
    heartbeat_at timestamptz
);
INSERT INTO ai.revocation_state (id, sequence) VALUES (1, 0);
CREATE TABLE ai.active_corpus (
    id integer PRIMARY KEY CHECK (id = 1),
    revision_id text REFERENCES ai.corpus_revisions,
    revocation_sequence bigint NOT NULL CHECK (revocation_sequence >= 0),
    activated_at timestamptz
);
INSERT INTO ai.active_corpus (id, revocation_sequence) VALUES (1, 0);
CREATE TABLE ai.rollback_corpus (
    slot integer PRIMARY KEY CHECK (slot BETWEEN 1 AND 2),
    revision_id text NOT NULL UNIQUE REFERENCES ai.corpus_revisions,
    retired_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL CHECK (expires_at > retired_at)
);
CREATE TABLE ai.documents (
    revision_id text NOT NULL REFERENCES ai.corpus_revisions,
    document_id uuid NOT NULL,
    place_id uuid NOT NULL,
    source_type text NOT NULL,
    source_id text NOT NULL,
    source_revision text NOT NULL,
    title text NOT NULL,
    published_at timestamptz NOT NULL,
    collected_at timestamptz NOT NULL,
    license_code text NOT NULL,
    region_code text NOT NULL,
    category_code text NOT NULL,
    content_hash text NOT NULL,
    normalized_text text NOT NULL CHECK (btrim(normalized_text) <> ''),
    eligibility_status text NOT NULL CHECK (eligibility_status = 'PUBLIC'),
    PRIMARY KEY (revision_id, document_id)
);
CREATE INDEX documents_scope ON ai.documents (revision_id, region_code, category_code, place_id);
CREATE INDEX documents_source ON ai.documents (source_type, source_id, source_revision);
CREATE TABLE ai.chunks (
    revision_id text NOT NULL,
    chunk_id uuid NOT NULL,
    document_id uuid NOT NULL,
    ordinal integer NOT NULL CHECK (ordinal >= 0),
    start_offset integer NOT NULL CHECK (start_offset >= 0),
    end_offset integer NOT NULL CHECK (end_offset > start_offset),
    chunk_text text NOT NULL CHECK (btrim(chunk_text) <> ''),
    content_hash text NOT NULL,
    search_text text NOT NULL CHECK (btrim(search_text) <> ''),
    search_tsv tsvector GENERATED ALWAYS AS (to_tsvector('simple', search_text)) STORED,
    PRIMARY KEY (revision_id, chunk_id),
    UNIQUE (revision_id, document_id, ordinal),
    FOREIGN KEY (revision_id, document_id) REFERENCES ai.documents
);
CREATE INDEX chunks_search_trgm ON ai.chunks USING gin (search_text gin_trgm_ops);
CREATE TABLE ai.embeddings (
    revision_id text NOT NULL,
    chunk_id uuid NOT NULL,
    embedding_profile_id text NOT NULL,
    embedding vector(384) NOT NULL,
    normalized boolean NOT NULL CHECK (normalized),
    PRIMARY KEY (revision_id, chunk_id, embedding_profile_id),
    FOREIGN KEY (revision_id, chunk_id) REFERENCES ai.chunks,
    FOREIGN KEY (revision_id, embedding_profile_id)
        REFERENCES ai.corpus_revisions (revision_id, embedding_profile_id),
    CHECK (abs(vector_norm(embedding) - 1.0) <= 0.0001)
);
CREATE TABLE ai.revocation_events (
    sequence bigint PRIMARY KEY CHECK (sequence > 0),
    scope text NOT NULL CHECK (scope IN ('SOURCE_REVISION','PLACE')),
    source_type text,
    source_id text,
    source_revision text,
    place_id uuid,
    revoked_at timestamptz NOT NULL DEFAULT now(),
    reason_code text NOT NULL,
    CHECK ((scope = 'PLACE' AND place_id IS NOT NULL AND source_type IS NULL
            AND source_id IS NULL AND source_revision IS NULL)
        OR (scope = 'SOURCE_REVISION' AND place_id IS NULL AND source_type IS NOT NULL
            AND source_id IS NOT NULL AND source_revision IS NOT NULL))
);
CREATE TABLE ai.source_revocations (
    source_type text NOT NULL,
    source_id text NOT NULL,
    source_revision text NOT NULL,
    last_sequence bigint NOT NULL REFERENCES ai.revocation_events,
    revoked_at timestamptz NOT NULL,
    PRIMARY KEY (source_type, source_id, source_revision)
);
CREATE TABLE ai.place_revocations (
    place_id uuid PRIMARY KEY,
    last_sequence bigint NOT NULL REFERENCES ai.revocation_events,
    revoked_at timestamptz NOT NULL
);
CREATE TABLE ai.corpus_sync_runs (
    run_id uuid PRIMARY KEY,
    revision_id text NOT NULL REFERENCES ai.corpus_revisions,
    manifest_hash text NOT NULL,
    state text NOT NULL CHECK (state IN ('RUNNING','SUCCEEDED','FAILED')),
    document_count bigint NOT NULL DEFAULT 0 CHECK (document_count >= 0),
    chunk_count bigint NOT NULL DEFAULT 0 CHECK (chunk_count >= 0),
    embedding_count bigint NOT NULL DEFAULT 0 CHECK (embedding_count >= 0),
    error_code text,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    lease_expires_at timestamptz
);
CREATE TABLE ai.revision_holds (
    hold_id uuid PRIMARY KEY,
    revision_id text NOT NULL REFERENCES ai.corpus_revisions,
    approved_by text NOT NULL,
    reason_code text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    expires_at timestamptz NOT NULL,
    CHECK (expires_at > created_at AND expires_at <= created_at + interval '30 days')
);
CREATE TABLE ai.gc_runs (
    run_id uuid PRIMARY KEY,
    state text NOT NULL CHECK (state IN ('RUNNING','SUCCEEDED','FAILED')),
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    actor text NOT NULL
);
CREATE TABLE ai.gc_checkpoints (
    run_id uuid NOT NULL REFERENCES ai.gc_runs,
    revision_id text NOT NULL,
    stage text NOT NULL CHECK (stage IN ('EMBEDDINGS','CHUNKS','DOCUMENTS','REVISION','DONE')),
    last_id uuid,
    deleted_count bigint NOT NULL DEFAULT 0 CHECK (deleted_count >= 0),
    PRIMARY KEY (run_id, revision_id)
);
-- Deliberately no revision FK: deletion evidence outlives the corpus itself.
CREATE TABLE ai.gc_audit (
    audit_id uuid PRIMARY KEY,
    run_id uuid NOT NULL REFERENCES ai.gc_runs,
    revision_id text NOT NULL,
    manifest_hash text NOT NULL,
    reason_code text NOT NULL,
    deleted_count bigint NOT NULL CHECK (deleted_count >= 0),
    deleted_bytes bigint NOT NULL CHECK (deleted_bytes >= 0),
    completed_at timestamptz NOT NULL DEFAULT now()
);
REVOKE ALL ON ALL TABLES IN SCHEMA ai FROM PUBLIC;
