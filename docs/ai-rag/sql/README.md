# 운영자 읽기 전용 집계 SQL

`embedding-inventory.sql`은 AI corpus migration [`001_corpus.sql`](../../../migrations/ai/001_corpus.sql)이 만든 `ai` 스키마를 대상으로 합니다. 임베딩 vector 값은 조회하지 않고 revision/profile별 행 수와 문서 지역별 분포만 반환합니다.

운영자는 production DB의 read-only role로 SQL 전체를 실행하고, 전체 `corpus_revision_id`, `is_active_revision`, `embedding_profile_id`, 지역별 `embedded_chunk_count`, `chunks_without_embedding` 결과를 AI팀에 전달합니다. AI팀은 운영 DB에 직접 접근하지 않습니다.

주요 테이블은 `ai.embeddings` (임베딩 행), `ai.chunks` (청크와 revision), `ai.documents` (문서와 `region_code`), `ai.corpus_revisions` (manifest/profile/count), `ai.active_corpus` (활성 revision pointer)입니다. 기존 `ai.corpus_revisions.embedding_count`는 적재 manifest 값이며 실제 현재 행 수 집계와 비교해야 합니다.

이 SQL 결과는 실행 시점에 따라 달라지므로 결과와 함께 실행 시각, DB 환경 식별자(민감한 host/endpoint 제외), query/tool 버전을 기록합니다. SQL은 transaction-level `READ ONLY` 모드로 실행됩니다.
