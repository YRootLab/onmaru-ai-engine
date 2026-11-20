-- PostgreSQL 17 + pg_search 0.27.0 must be supplied by the database image.
-- Search text uses character n-grams so Korean queries such as '한옥' match.
-- Run in one transaction with bounded maintenance memory for small production DBs.
BEGIN;
SET LOCAL maintenance_work_mem = '32MB';
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_extension
         WHERE extname = 'pg_search' AND extversion = '0.27.0'
    ) THEN
        RAISE EXCEPTION 'pg_search 0.27.0 is required before applying 004_pg_search_bm25.sql';
    END IF;
END
$$;

ALTER TABLE ai.chunks
    ADD COLUMN search_key text
    GENERATED ALWAYS AS (revision_id || ':' || chunk_id::text) STORED;

CREATE UNIQUE INDEX chunks_search_key_unique ON ai.chunks (search_key);

CREATE INDEX chunks_search_bm25_idx
    ON ai.chunks
    USING bm25 (
        search_key,
        revision_id,
        document_id,
        (search_text::pdb.ngram(2, 3))
    ) WITH (key_field = 'search_key');

ANALYZE ai.documents;
ANALYZE ai.chunks;
COMMIT;
