"""Read-only deployment gate for the production retrieval prerequisites."""
from __future__ import annotations

import psycopg

from onmaru_ai.embedding import E5_SMALL_ONNX_INT8_384


def corpus_ready(connection: psycopg.Connection[tuple[object, ...]]) -> bool:
    row = connection.execute(
        """SELECT EXISTS (
             SELECT 1 FROM ai.active_corpus a
             JOIN ai.corpus_revisions r USING (revision_id)
             JOIN ai.revocation_state s ON s.id=a.id
             WHERE a.id=1 AND r.state='ACTIVE' AND r.gc_state='LIVE'
               AND r.embedding_profile_id=%s
               AND a.revocation_sequence=s.sequence
               AND s.source_snapshot_watermark IS NOT NULL
               AND s.heartbeat_at BETWEEN clock_timestamp()-interval '60 seconds'
                   AND clock_timestamp()
               AND r.document_count>0 AND r.chunk_count>0 AND r.embedding_count>0
               AND EXISTS (SELECT 1 FROM ai.reviewed_facts f
                 WHERE f.revision_id=r.revision_id AND f.review_status='APPROVED')
           ) AND EXISTS (SELECT 1 FROM pg_extension
               WHERE extname='pg_search' AND extversion='0.27.0')
             AND EXISTS (SELECT 1 FROM pg_index i
               WHERE i.indexrelid=to_regclass('ai.chunks_search_bm25_idx')
                 AND i.indisvalid AND i.indisready)""",
        (E5_SMALL_ONNX_INT8_384.profile_id,),
    ).fetchone()
    return row is not None and row[0] is True


def runtime_corpus_ready(dsn: str) -> bool:
    try:
        with psycopg.connect(
            dsn, connect_timeout=2,
            options='-c default_transaction_read_only=on -c statement_timeout=1500',
        ) as connection:
            return corpus_ready(connection)
    except Exception:
        return False
