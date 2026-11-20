# Plan/Execute staging 준비 절차

> 상태: AI Engine PR #84가 `develop`에 병합됐다. 아래 절차는 staging/운영 handoff이며, PostgreSQL migration, corpus 재색인, fact 적재 또는 feature flag 변경을 이미 수행했다는 뜻은 아니다.

## 첫 오픈 범위와 차단 조건 (2026-11-20)

- **E5 임베딩:** Gemini는 근거 기반 답변 생성에만 사용한다. pinned local E5 ONNX query/passage가 같은 프로필을 사용한다. Corpus는 새 revision으로만 적재하고, 스풀 파일과 resume 옵션으로 중단 후 재개한다.
- **BM25:** PostgreSQL 17의 pg_search 0.27.0과 pdb.ngram(2,3) BM25 인덱스가 필수다. migration 004_pg_search_bm25.sql 적용 및 실제 한옥 쿼리/EXPLAIN 확인 전에는 lexical/hybrid route를 활성화하지 않는다.
- **Reranker:** 첫 오픈은 Hybrid+RRF 후 기존 passthrough 순위를 사용한다. Cross-Encoder는 512MB RSS와 15초 제한에서 품질·지연 평가를 마친 뒤 별도 출시로 미룬다.
- **Reviewed facts와 heartbeat:** 사람이 승인한 fact가 활성 revision에 1건 이상 있어야 하고 revocation heartbeat가 60초 이내여야 한다. 자동 문장 추출은 검토 대기 후보만 만든다. AI Engine은 source-of-truth heartbeat를 자체 갱신하지 않는다.
- **Gemini quota:** AI Engine은 provider의 429를 HTTP 429와 AI_QUOTA_EXCEEDED로 Spring에 전달한다. Spring은 유효한 baseline을 만들고 engine=BASELINE, degradedReason=AI_QUOTA_EXCEEDED와 안내 배너로 응답한다. baseline도 불가능하면 Spring이 명시적 실패로 끝낸다. SSE는 이미 200으로 시작할 수 있으므로 종료 error 이벤트의 quota 코드를 매핑한다.

기능 플래그 전환 전에는 새 E5 revision의 검색 평가, reviewed facts 적재·span 검증, revocation heartbeat, Spring 버전 4개 값 동기화 및 실제 Spring↔AI HTTP smoke를 모두 마친다. 값 확인에는 scripts/print_active_runtime_versions.py를 사용한다.

## 현재 코드가 요구하는 설정

AI Engine `ai-engine` 컨테이너에는 다음 설정을 전달한다.

| 변수 | 필요 여부 | 의미 |
|---|---|---|
| `ONMARU_AI_DB_DSN` | Plan/Execute 사용 시 필수 | `ai` schema 읽기와 retrieval에 사용할 **runtime role** 접속 문자열. migration role credential을 넣지 않는다. 기존 alias `ONMARU_DB_URL`도 읽지만 Compose 계약은 `ONMARU_AI_DB_DSN`으로 통일한다. |
| `ONMARU_SECRET_GEMINI_API_KEY_CURRENT` | 현재 app 시작 시 필수 | secret provider의 `gemini.api-key` 값. 검수 근거를 이용한 답변 생성에 사용한다. |
| `ONMARU_E5_ONNX_DIR` | 기본값 `/opt/onmaru/e5` | Docker image build에서 생성·검증한 pinned E5 ONNX artifact 디렉터리. 실행 중 모델 다운로드는 하지 않는다. |
| `ONMARU_SPRING_BASE_URL` | 배포에서 필수 권장 | Spring 내부 origin. 기본값은 `http://staging-api:8080`이므로 운영 Compose는 반드시 명시한다. |
| `ONMARU_GEMINI_MODEL_NAME` | 선택 | grounded claim 생성 모델명. 기본값은 `gemini-2.5-flash`; 배포 전 실제 지원 모델과 비용 설정을 확인한다. |

Gemini는 검수된 근거를 바탕으로 답변을 생성할 때만 사용한다. Query/passage embedding은 같은 로컬 E5 ONNX CPU artifact를 사용하며 활성 corpus profile은 `multilingual-e5-small-384-onnx-int8@614241f622f5`와 일치해야 한다. Docker image build에서 pinned artifact를 생성해 image에 포함하므로 실행 중 모델 다운로드나 별도 model volume은 없다. 앱 컨테이너에는 database 내부 network 연결을 허용하되 DB port를 host에 공개하지 않는다. migration 계정은 Compose의 AI Engine runtime env로 전달하지 않는다.

## Embedding profile 결정

선택한 이행안은 **고정된 로컬 E5 ONNX artifact로 별도 staging revision을 적재하고 검증한 다음 활성화하는 것**이다. 기존 active revision은 staging 검증과 rollback 판단 전까지 보존한다. 운영 corpus를 직접 덮어쓰지 않는다.

기존 E5 revision의 생성 기록을 inventory로 확인한다. 아래 export 명령은 pinned E5 commit을 dynamic-int8 ONNX artifact로 내보낸다. 이 프로파일은 기존 FP32 profile과 구별되므로 새 revision을 적재한다. Hash backend는 `deterministic-hash-384@local-only`로 표시되며 `--hash-only --dry-run` 외에는 사용할 수 없다. Corpus ingestion에는 Gemini key를 전달하지 않는다.

Artifact export는 CI/Docker image build에서 pinned E5 commit으로 실행된다. 로컬 Linux에서 별도 artifact가 필요하면 `uv run --group embedding-export python scripts/export_e5_onnx.py --output <artifact-dir>`를 사용할 수 있다. Mac Intel에서는 ONNX artifact를 Docker build로 생성한다.

KTO catalog corpus는 활성화와 분리해 먼저 적재한다. `AI_CORPUS_WRITE_DSN`은 one-off AI migration/corpus-writer role, `CATALOG_READ_DSN`은 공개 catalog read role의 접속 문자열로 운영자 환경에서 구성한다. 둘 다 Compose runtime env에 저장하지 않는다.

```bash
# `AI_ENGINE_SERVICE=staging-ai-engine` in staging, `ai-engine` in production.
docker volume create onmaru-ai-corpus-stage
docker compose --profile ai-engine run --rm \
  -v onmaru-ai-corpus-stage:/app/.onmaru-corpus-staging \
  -e ONMARU_AI_DB_DSN -e ONMARU_AI_CATALOG_READ_DSN \
  "$AI_ENGINE_SERVICE" \
  python scripts/ingest_catalog_from_postgres.py \
  --revision-id "$STAGING_E5_REVISION" \
  --spool-path "/app/.onmaru-corpus-staging/$STAGING_E5_REVISION.sqlite"
```

이 호출 전에 one-off runner environment로 `ONMARU_AI_DB_DSN=$AI_CORPUS_WRITE_DSN`, `ONMARU_AI_CATALOG_READ_DSN=$CATALOG_READ_DSN`을 전달한다. `docker compose run -e NAME` passthrough를 사용하고 DSN을 CLI 인자로 넣지 않는다. E5 artifact는 검토·병합된 image에 포함되어 있어야 한다.

`--resume`은 같은 named volume과 같은 spool path를 유지하며 재실행할 때만 추가한다. 스풀은 장소별 청크/벡터를 저장하므로 운영 재색인 전에 named volume의 여유 공간을 확인하고, staged DB revision 검증 및 rollback 보존이 끝난 뒤에만 해당 spool 파일을 삭제한다.

적재 완료 후 `ai.corpus_revisions`의 profile이 `multilingual-e5-small-384-onnx-int8@614241f622f5`인지, 저장된 문서·청크·embedding 수와 실제 count가 같은지 확인한다. 그런 다음 revision을 먼저 read-only 검사한다:

```bash
docker compose --profile ai-engine run --rm -e ONMARU_AI_DB_DSN "$AI_ENGINE_SERVICE" \
  python scripts/activate_corpus_revision.py \
     --revision-id "$STAGING_E5_REVISION" \
     --confirm-revision "$STAGING_E5_REVISION"
```

read-only 결과를 검토한 뒤에만 같은 명령에 `--apply`를 추가해 활성화한다. activator는 정확한 revision 재확인, E5 ONNX profile, 상태, count 정합성, revocation heartbeat를 점검하고 저장소의 optimistic concurrency 검사로 pointer를 전환한다. 기존 active revision은 rollback 판단이 끝날 때까지 보존한다.

Revision이 바뀌면 reviewed facts의 `revisionId`, `chunkId`, offsets도 새 revision과 대조해야 한다. 원문/청크 내용이 같다는 이유만으로 기존 fact row를 자동 복사하거나 승인으로 간주하지 않는다. 사람 검수 결과와 exact span을 확인해 별도 JSONL로 재적재한다.

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

적재가 중단되면 같은 revision과 spool 경로를 지정해 `--resume`을 추가한다. 스풀은 catalog active revision과 최초 수집 timestamp를 고정하므로 원천 catalog revision이 바뀌면 기존 스풀을 거부한다. 운영 적재 전 별도 staging replica에서 전체 23,573건 dry-run을 마치고 spool 크기·시간·manifest hash를 기록한다.

## pg_search 0.27.0 migration과 한국어 query

DB image에 설치된 확장 버전을 확인한 뒤 AI migration role로 migration을 적용한다. migration은 extension을 설치하지 않으며 잘못된 버전에서 실패한다. 인덱스 빌드 트랜잭션은 `maintenance_work_mem=32MB`로 제한하고 migration 끝에서 두 테이블을 `ANALYZE`한다. 320MB 운영 DB에서는 staging 동등 환경에서 빌드 RSS와 잠금 시간을 확인한 후 적용한다:

```bash
psql "$AI_MIGRATION_DSN" -v ON_ERROR_STOP=1 \
  -f migrations/ai/004_pg_search_bm25.sql
```

성공 로그에 `ANALYZE` 및 `COMMIT`이 포함되어야 한다. 인덱스 생성 도중 실패하면 transaction 전체가 rollback되므로 로그와 DB index 목록을 확인한 뒤 재시도한다.

검증은 PostgreSQL 17 + pg_search 0.27.0 운영과 같은 image에서 한다:

```sql
SELECT extversion FROM pg_extension WHERE extname='pg_search';
SELECT c.chunk_id, pdb.score(c.search_key) AS score
FROM ai.chunks c
WHERE c.revision_id='<active_revision>'
  AND c.search_text @@@ pdb.parse('한옥')
ORDER BY pdb.score(c.search_key) DESC, c.chunk_id
LIMIT 20;
EXPLAIN (ANALYZE, BUFFERS)
SELECT c.chunk_id, pdb.score(c.search_key) AS score
FROM ai.chunks c
WHERE c.revision_id='<active_revision>'
  AND c.search_text @@@ pdb.parse('한옥')
ORDER BY pdb.score(c.search_key) DESC, c.chunk_id
LIMIT 20;
```

`한옥` 결과가 없거나 plan에서 `chunks_search_bm25_idx`가 사용되지 않으면 lexical route를 켜지 않는다. 실제 version과 ngram index definition은 Engine repository가 시작 시 확인한다.

사람 검수 queue의 exact span 후보는 다음 read-only exporter로 만들 수 있다. 출력의 모든 row는 `NEEDS_HUMAN_REVIEW`이며 `load_reviewed_facts.py` 입력이 아니다. 콘텐츠 담당자는 의미·종류·시간성·관계·승인자를 검토하고 loader 계약에 맞는 승인 JSONL을 별도로 작성해야 한다:

```bash
docker compose --profile ai-engine run --rm -e ONMARU_AI_DB_DSN \
  "$AI_ENGINE_SERVICE" python scripts/export_reviewed_fact_candidates.py \
    --revision-id "$ACTIVE_E5_REVISION" \
    --output /tmp/review-candidates.jsonl
```

적재 후 활성 코퍼스 버전과 운영 준비도를 조회한다:

```bash
docker compose --profile ai-engine run --rm -e ONMARU_AI_DB_DSN \
  "$AI_ENGINE_SERVICE" python scripts/print_active_runtime_versions.py
```

출력이 stale heartbeat 또는 no reviewed facts로 종료되면 Spring `.env`에 값을 복사하거나 feature flag를 켜지 않는다. 정상 출력의 네 값(`CORPUS_REVISION`, `CONFIG_HASH`, `QUESTION_DICTIONARY_VERSION`, `SOURCE_REVOCATION_SEQUENCE`)을 Spring 운영 owner가 설정하고 readiness 응답과 대조한다. Heartbeat는 Spring revocation source가 sequence를 확인한 뒤 60초 주기로 갱신해야 하며 AI Engine이 대신 heartbeat를 써서는 안 된다.


## 남은 blocker

- AI Engine PR #84와 BE PR #862가 각각 develop에 병합됐다. 다음은 staging 배선·재색인·migration·검수 fact 적재와 Spring↔AI live HTTP E2E다.
- production active corpus inventory와 embedding profile을 재확인해야 한다. 저장소 handoff에 남은 E5 정보는 이전 inventory 기록이다.
- JSONL parser/loader와 별도 corpus activator는 구현됐지만, 실제 curated fact set·reviewer 승인·감사 절차는 BE/content owner가 준비해야 한다.
- PostgreSQL migration은 여기서 실행하지 않았다. runtime role grant도 실제 role명을 모르는 상태에서 적용하지 않았다.
- Spring 계약 테스트 통과는 live HTTP 합동 E2E 통과를 의미하지 않는다.
