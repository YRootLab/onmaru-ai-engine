-- PostgreSQL 17. Run as the AI migration owner.
-- Records approved RAG evaluation decisions and operational gate outcomes.

CREATE TABLE IF NOT EXISTS ai.rag_activation_decisions (
    id bigserial PRIMARY KEY,
    corpus_revision_id text NOT NULL REFERENCES ai.corpus_revisions (revision_id),
    candidate_policy text NOT NULL,
    image_digest text NOT NULL,
    embedding_profile text NOT NULL,
    dataset_input_sha256 text NOT NULL,
    dataset_gold_sha256 text NOT NULL,
    enabled boolean NOT NULL,
    action text NOT NULL CHECK (action IN ('ACTIVATE', 'ROLLBACK')),
    reason text NOT NULL,
    baseline_passed boolean NOT NULL,
    candidate_passed boolean NOT NULL,
    metric_deltas jsonb NOT NULL DEFAULT '{}'::jsonb,
    evaluated_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_rag_activation_corpus_eval 
    ON ai.rag_activation_decisions (corpus_revision_id, evaluated_at DESC);

REVOKE ALL ON ai.rag_activation_decisions FROM PUBLIC;
