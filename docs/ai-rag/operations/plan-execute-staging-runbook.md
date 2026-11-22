# Plan/Execute staging 준비 절차

> 상태: AI Engine PR #84가 `develop`에 병합됐다. 아래 절차는 staging/운영 handoff이며, PostgreSQL migration, corpus 재색인, fact 적재 또는 feature flag 변경을 이미 수행했다는 뜻은 아니다.

## 현재 코드가 요구하는 설정

AI Engine `ai-engine` 컨테이너에는 다음 설정을 전달한다.

| 변수 | 필요 여부 | 의미 |
|---|---|---|
| `ONMARU_AI_DB_DSN` | Plan/Execute 사용 시 필수 | `ai` schema 읽기와 retrieval에 사용할 **runtime role** 접속 문자열. migration role credential을 넣지 않는다. 기존 alias `ONMARU_DB_URL`도 읽지만 Compose 계약은 `ONMARU_AI_DB_DSN`으로 통일한다. |
| `ONMARU_AI_REVOCATION_SYNC_DSN` | DB 연결을 사용하는 상시 AI Engine에서 필수 | revocation snapshot/event와 heartbeat를 반영할 전용 sync role 접속 문자열. runtime DSN으로 대체하지 않는다. 이 값이 없거나 poller가 현재 watermark를 따라잡지 못하면 `/ready`는 503이다. |
| `ONMARU_SECRET_GEMINI_API_KEY_CURRENT` | 현재 app 시작 시 필수 | secret provider의 `gemini.api-key` 값. Plan/Execute 생성 및 Gemini query embedding에 쓰인다. |
| `ONMARU_SPRING_BASE_URL` | 배포에서 필수 권장 | Spring 내부 origin. 기본값은 `http://staging-api:8080`이므로 운영 Compose는 반드시 명시한다. |
| `ONMARU_GEMINI_MODEL_NAME` | 선택 | grounded claim 생성 모델명. 기본값은 `gemini-2.5-flash`; 배포 전 실제 지원 모델과 비용 설정을 확인한다. |

현재 Plan/Execute의 query embedding은 코드에 `gemini-embedding-001-384@v1`로 고정되어 있고 profile override env는 없다. 따라서 활성 corpus도 같은 profile이어야 dense route가 동작한다. profile 선택을 임의의 Compose env로 흉내 내지 않는다. 앱 컨테이너에는 database 내부 network 연결을 허용하되 DB port를 host에 공개하지 않는다. migration 계정은 Compose의 AI Engine runtime env로 전달하지 않는다.

`ONMARU_AI_REVOCATION_SYNC_DSN`은 corpus migration owner와 분리한다. AI migration `005_source_revocation_bootstrap.sql` 적용 후 DB 관리자 계정으로 아래 별도 그룹과 login을 준비하고, 비밀번호는 Compose `.env`/secret store에서 주입한다. 운영 DB에 이미 migration role과 runtime role이 있으므로 기존 두 역할은 재사용하지 않는다.

```sql
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='onmaru_ai_revocation_sync') THEN
    CREATE ROLE onmaru_ai_revocation_sync NOLOGIN;
  END IF;
END
$$;
CREATE ROLE onmaru_ai_revocation_sync_login LOGIN PASSWORD '<새 랜덤 비밀번호>';
GRANT onmaru_ai_revocation_sync TO onmaru_ai_revocation_sync_login;
GRANT USAGE ON SCHEMA ai TO onmaru_ai_revocation_sync;
GRANT SELECT, UPDATE ON ai.revocation_state, ai.active_corpus
  TO onmaru_ai_revocation_sync;
GRANT SELECT, INSERT, DELETE ON ai.revocation_events,
  ai.source_revocations, ai.place_revocations TO onmaru_ai_revocation_sync;
GRANT SELECT, INSERT, UPDATE, DELETE ON ai.revocation_snapshot_staging_state,
  ai.revocation_snapshot_staging_events, ai.revocation_snapshot_staging_places
  TO onmaru_ai_revocation_sync;
```

BE의 `infra/lightsail/.env`에는 `ONMARU_DB_AI_REVOCATION_SYNC_USER`와 새 `ONMARU_DB_AI_REVOCATION_SYNC_PASSWORD`를 넣고 AI 전용 DSN을 compose가 컨테이너에 전달하게 한다. `ONMARU_AI_DB_DSN`은 계속 읽기 전용이다. sync credential 또는 최초 snapshot/heartbeat가 준비되지 않으면 앱은 의도적으로 readiness를 통과하지 않는다.

## Embedding profile 결정

이번 코드와 맞는 기본 이행안은 **Gemini profile로 staging corpus를 새 revision에 재색인하고 검증한 다음 활성화하는 것**이다. 기존 active revision은 staging 검증과 rollback 판단 전까지 보존한다. 운영 corpus를 직접 덮어쓰지 않는다.

기존 E5 revision이 진짜 `intfloat/multilingual-e5-small` 모델로 만들어졌는지 먼저 inventory와 ingest 기록으로 확인한다. 이제 두 ingestion CLI는 key가 없으면 실패하고, hash backend는 `deterministic-hash-384@local-only`로 표시되며 `--hash-only --dry-run` 외에는 사용할 수 없다. API key는 `ONMARU_SECRET_GEMINI_API_KEY_CURRENT` 환경 secret으로만 전달한다. CLI 인자로 전달하지 않는다.

KTO catalog corpus는 활성화와 분리해 먼저 적재한다. `AI_CORPUS_WRITE_DSN`은 one-off AI migration/corpus-writer role, `CATALOG_READ_DSN`은 공개 catalog read role의 접속 문자열로 운영자 환경에서 구성한다. 둘 다 Compose runtime env에 저장하지 않는다.

```bash
# `AI_ENGINE_SERVICE=staging-ai-engine` in staging, `ai-engine` in production.
docker compose --profile ai-engine run --rm \
  -e ONMARU_AI_DB_DSN -e ONMARU_AI_CATALOG_READ_DSN \
  -e ONMARU_SECRET_GEMINI_API_KEY_CURRENT \
  "$AI_ENGINE_SERVICE" \
  python scripts/ingest_catalog_from_postgres.py \
  --revision-id "$STAGING_GEMINI_REVISION"
```

이 호출 전에 one-off runner environment로 `ONMARU_AI_DB_DSN=$AI_CORPUS_WRITE_DSN`, `ONMARU_AI_CATALOG_READ_DSN=$CATALOG_READ_DSN`, `ONMARU_SECRET_GEMINI_API_KEY_CURRENT`를 secret injection으로 전달한다. `docker compose run -e NAME` passthrough를 사용하고 DSN이나 Gemini key를 CLI 인자로 넣지 않는다.

적재 완료 후 `ai.corpus_revisions`의 profile이 `gemini-embedding-001-384@v1`인지, 저장된 문서·청크·embedding 수와 실제 count가 같은지 확인한다. 그런 다음 revision을 먼저 read-only 검사한다:

```bash
docker compose --profile ai-engine run --rm -e ONMARU_AI_DB_DSN "$AI_ENGINE_SERVICE" \
  python scripts/activate_corpus_revision.py \
  --revision-id "$STAGING_GEMINI_REVISION" \
  --confirm-revision "$STAGING_GEMINI_REVISION"
```

read-only 결과를 검토한 뒤에만 같은 명령에 `--apply`를 추가해 활성화한다. activator는 정확한 revision 재확인, Gemini profile, 상태, count 정합성, revocation heartbeat를 점검하고 저장소의 optimistic concurrency 검사로 pointer를 전환한다. 기존 active revision은 rollback 판단이 끝날 때까지 보존한다.

Gemini API 비용·지연 또는 데이터 정책 때문에 E5를 유지하기로 결정한다면, 실제 고정 모델 artifact를 로드하고 profile identity를 검증하는 E5 `EmbeddingBackend`를 먼저 구현·테스트해야 한다. 현재 Plan/Execute에는 E5 backend가 없으므로 E5 유지 상태에서 dense route를 켜면 안 된다.

## `003_reviewed_facts.sql` 적용과 fact 검수

1. 변경이 검토·병합된 AI Engine release를 고정하고 staging DB backup/restore 절차를 확인한다.
2. 배포 artifact의 migration을 `ONMARU_DB_AI_MIGRATION_USER`에 해당하는 별도 migration role로 staging DB에 한 번 적용한다. AI Engine runtime role을 migration에 사용하지 않는다.

   ```bash
   psql "$AI_MIGRATION_DSN" -v ON_ERROR_STOP=1 \
     -f migrations/ai/003_reviewed_facts.sql
   ```

3. migration owner로 실행 권한을 구성한다. runtime role 이름은 환경별 실제 role을 확인한 뒤 치환한다:

   ```sql
   GRANT USAGE ON SCHEMA ai TO <ai_runtime_role>;
   GRANT SELECT ON ai.reviewed_facts TO <ai_runtime_role>;
   ```

   이 표는 새 fact table에 필요한 최소 권한이다. corpus의 기존 테이블 권한은 별도 기존 권한 정책을 따른다.
4. 장소별 public source 자료를 사람이 검토해 사실 단위로 선별한다. 검색 chunk를 자동 승인하거나 모델이 만든 문장을 fact로 적재하지 않는다. 공개 계약의 `placeId`는 `ai.documents.source_id`와 같아야 한다. `chunk_id`, offset, 문장 원문은 active revision 문서와 정확히 일치해야 한다.
5. 승인된 fact는 감사 가능한 JSONL artifact로 준비하고 reviewer, 승인 시각, source revision을 기록한다. loader는 승인 여부를 결정하지 않는다. 각 row의 `factText`는 원문 내 exact span이어야 하고 reviewer 메타데이터가 이미 있어야 한다. 한 줄에 JSON object 하나를 쓰며 필드는 `revisionId`, `factId`, `chunkId`(UUID), `placeId`(public ID), `startOffset`, `endOffset`, `factText`, `kind`, `supportType`, `timeScope`, `relation`, `reviewStatus`(`APPROVED`), `approvedBy`, `approvedAt`(timezone 포함)이다. `relation`은 null 또는 generation `VerifiedRelation` schema다. `scripts/load_reviewed_facts.py --help`와 `ReviewedFactImport` 모델이 입력 계약이다.
6. runtime role과 분리된 일회성 fact loader role에 필요한 최소 권한을 migration owner가 부여한다. 실제 role 이름은 staging DB에서 확인한다:

   ```sql
   GRANT USAGE ON SCHEMA ai TO <ai_fact_loader_role>;
   GRANT SELECT ON ai.active_corpus, ai.revocation_state, ai.corpus_revisions,
     ai.documents, ai.chunks, ai.place_revocations, ai.source_revocations
     TO <ai_fact_loader_role>;
   GRANT INSERT ON ai.reviewed_facts TO <ai_fact_loader_role>;
   ```

   migration owner는 runtime role에 별도로 `SELECT ON ai.reviewed_facts`만 부여한다. fact loader credential은 Compose에 넣지 않고, 적재 후 일회성 권한을 revoke한다.
7. 먼저 기본 read-only 검증을 실행한다. 출력 count와 오류를 확인하고, 그 후에만 `--apply`를 추가해 전체 JSONL을 단일 transaction으로 적재한다:

   ```bash
   docker compose --profile ai-engine run --rm \
     -e ONMARU_AI_DB_DSN \
     -v "$PWD/$REVIEWED_FACTS_JSONL:/tmp/reviewed-facts.jsonl:ro" \
     "$AI_ENGINE_SERVICE" python scripts/load_reviewed_facts.py \
       --input /tmp/reviewed-facts.jsonl

   docker compose --profile ai-engine run --rm \
     -e ONMARU_AI_DB_DSN \
     -v "$PWD/$REVIEWED_FACTS_JSONL:/tmp/reviewed-facts.jsonl:ro" \
     "$AI_ENGINE_SERVICE" python scripts/load_reviewed_facts.py \
       --input /tmp/reviewed-facts.jsonl --apply
   ```

8. 다음 확인 쿼리에서 불일치가 0건인지 확인하고, 승인 fact 수와 표본을 콘텐츠 담당자가 재검토한다:

   ```sql
   SELECT f.revision_id, count(*) AS approved_fact_count
   FROM ai.reviewed_facts f
   WHERE f.review_status = 'APPROVED'
   GROUP BY f.revision_id;

   SELECT f.fact_id, f.place_id, f.fact_text
   FROM ai.reviewed_facts f
   JOIN ai.chunks c USING (revision_id, chunk_id)
   JOIN ai.documents d USING (revision_id, document_id)
   WHERE f.review_status = 'APPROVED'
     AND (d.source_id <> f.place_id
       OR d.eligibility_status <> 'PUBLIC'
       OR f.start_offset < c.start_offset
       OR f.end_offset > c.end_offset
       OR substring(d.normalized_text FROM f.start_offset + 1
                    FOR f.end_offset - f.start_offset) <> f.fact_text);
   ```

   두 번째 쿼리는 0행이어야 한다. 이 검증은 의미 검수나 Spring 최종 공개 자격 검사를 대체하지 않는다.

## Spring과 합동 staging 검증 순서

1. BE와 AI Engine의 승인된 PR/image digest 및 migration version을 함께 고정한다. 두 저장소의 uncommitted 상태를 직접 staging에 배포하지 않는다.
2. staging에서 AI DB runtime role의 schema 접근, 활성 corpus revision/profile, secret 주입, Spring 내부 URL, AI readiness를 확인한다. 준비가 모두 끝날 때까지 `onmaru.ai.plan-execute-enabled=false`를 유지한다.
3. 동일 trace/run으로 `CLARIFY_OR_SCOPE`(execute 0회), `SQL_ONLY + NO_MATCH`, pinned IDs가 있어도 `placeIds=null`인 일반 추천, 그리고 SQL_ONLY/LEXICAL_ONLY/DENSE_ONLY/HYBRID/SQL_PLUS_RETRIEVAL 5개 route를 실제 Spring↔AI HTTP로 검증한다.
4. 각 route에서 승인·제외·revocation 필터, grounding/evidence, timeout/fallback, 기존 board/state 보존, 로그상 corpus/profile/config version을 확인한다. `SQL_PLUS_RETRIEVAL`의 Spring 장소 응답은 corpus evidence로 직접 사용하지 않으며, 같은 Postgres snapshot에서 해당 장소 ID에 연결된 승인 fact와 exact source span을 찾은 경우에만 generation에 전달한다. 검수 fact가 없으면 빈 evidence 결과가 정상 fail-closed 동작이다. 기능·품질·지연·메모리 결과를 기록한다.
5. 검증 결과를 BE와 AI Engine 양쪽 PR에 연결한다. 그 다음 별도 rollout 승인에 따라 staging flag부터 단계적으로 변경한다. 운영 flag는 staging 결과, rollback rehearsal, 배포 승인 전까지 false로 유지한다.

## 남은 blocker

- AI Engine PR #84와 BE PR #862가 각각 develop에 병합됐다. 다음은 staging 배선·재색인·migration·검수 fact 적재와 Spring↔AI live HTTP E2E다.
- production active corpus inventory와 embedding profile을 재확인해야 한다. 저장소 handoff에 남은 E5 정보는 이전 inventory 기록이다.
- JSONL parser/loader와 별도 corpus activator는 구현됐지만, 실제 curated fact set·reviewer 승인·감사 절차는 BE/content owner가 준비해야 한다.
- PostgreSQL migration은 여기서 실행하지 않았다. runtime role grant도 실제 role명을 모르는 상태에서 적용하지 않았다.
- Spring 계약 테스트 통과는 live HTTP 합동 E2E 통과를 의미하지 않는다.
