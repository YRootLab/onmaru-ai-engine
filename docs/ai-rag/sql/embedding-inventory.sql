-- Read-only inventory for an operator to run against the production PostgreSQL database.
-- Tables are owned by the AI service: ai.embeddings, ai.chunks, ai.documents,
-- ai.corpus_revisions and ai.active_corpus. This does not reveal vector values.

BEGIN TRANSACTION READ ONLY;

-- Per revision/profile totals and regional distribution. LEFT JOINs retain regions
-- with documents that currently have no matching embedding rows.
SELECT
    r.revision_id AS corpus_revision_id,
    a.revision_id = r.revision_id AS is_active_revision,
    r.state AS revision_state,
    r.embedding_profile_id,
    d.region_code,
    count(DISTINCT d.document_id) AS document_count,
    count(DISTINCT c.chunk_id) AS chunk_count,
    count(DISTINCT e.chunk_id) AS embedded_chunk_count,
    count(DISTINCT c.chunk_id) - count(DISTINCT e.chunk_id) AS chunks_without_embedding
FROM ai.corpus_revisions AS r
LEFT JOIN ai.active_corpus AS a ON a.id = 1
LEFT JOIN ai.documents AS d ON d.revision_id = r.revision_id
LEFT JOIN ai.chunks AS c
    ON c.revision_id = d.revision_id AND c.document_id = d.document_id
LEFT JOIN ai.embeddings AS e
    ON e.revision_id = c.revision_id
   AND e.chunk_id = c.chunk_id
   AND e.embedding_profile_id = r.embedding_profile_id
GROUP BY r.revision_id, a.revision_id, r.state, r.embedding_profile_id, d.region_code
ORDER BY is_active_revision DESC, r.revision_id, d.region_code NULLS FIRST;

-- Compact revision/profile totals for dashboards and release evidence.
SELECT
    r.revision_id AS corpus_revision_id,
    a.revision_id = r.revision_id AS is_active_revision,
    r.state AS revision_state,
    r.embedding_profile_id,
    r.document_count AS manifest_document_count,
    r.chunk_count AS manifest_chunk_count,
    r.embedding_count AS manifest_embedding_count,
    count(DISTINCT e.chunk_id) AS actual_embedding_count,
    count(DISTINCT e.chunk_id) FILTER (WHERE lower(d.region_code) = 'kr-11') AS kr_11_embedding_count
FROM ai.corpus_revisions AS r
LEFT JOIN ai.active_corpus AS a ON a.id = 1
LEFT JOIN ai.embeddings AS e
    ON e.revision_id = r.revision_id
   AND e.embedding_profile_id = r.embedding_profile_id
LEFT JOIN ai.chunks AS c
    ON c.revision_id = e.revision_id AND c.chunk_id = e.chunk_id
LEFT JOIN ai.documents AS d
    ON d.revision_id = c.revision_id AND d.document_id = c.document_id
GROUP BY r.revision_id, a.revision_id, r.state, r.embedding_profile_id,
         r.document_count, r.chunk_count, r.embedding_count
ORDER BY is_active_revision DESC, r.revision_id;

COMMIT;
