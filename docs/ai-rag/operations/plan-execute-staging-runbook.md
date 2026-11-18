# Plan/Execute staging 준비 절차

> 상태: AI Engine feature branch의 코드 기준 운영 handoff 초안. 운영 migration, corpus 재색인, fact 적재 또는 feature flag 변경을 수행했다는 뜻은 아니다.

## 현재 코드가 요구하는 설정

AI Engine `ai-engine` 컨테이너에는 다음 설정을 전달한다.

| 변수 | 필요 여부 | 의미 |
|---|---|---|
| `ONMARU_AI_DB_DSN` | Plan/Execute 사용 시 필수 | `ai` schema 읽기와 retrieval에 사용할 **runtime role** 접속 문자열. migration role credential을 넣지 않는다. 기존 alias `ONMARU_DB_URL`도 읽지만 Compose 계약은 `ONMARU_AI_DB_DSN`으로 통일한다. |
| `ONMARU_SECRET_GEMINI_API_KEY_CURRENT` | 현재 app 시작 시 필수 | secret provider의 `gemini.api-key` 값. Plan/Execute 생성 및 Gemini query embedding에 쓰인다. |
| `ONMARU_SPRING_BASE_URL` | 배포에서 필수 권장 | Spring 내부 origin. 기본값은 `http://staging-api:8080`이므로 운영 Compose는 반드시 명시한다. |
| `ONMARU_GEMINI_MODEL_NAME` | 선택 | grounded claim 생성 모델명. 기본값은 `gemini-2.5-flash`; 배포 전 실제 지원 모델과 비용 설정을 확인한다. |

현재 Plan/Execute의 query embedding은 코드에 `gemini-embedding-001-384@v1`로 고정되어 있고 profile override env는 없다. 따라서 활성 corpus도 같은 profile이어야 dense route가 동작한다. profile 선택을 임의의 Compose env로 흉내 내지 않는다. 앱 컨테이너에는 database 내부 network 연결을 허용하되 DB port를 host에 공개하지 않는다. migration 계정은 Compose의 AI Engine runtime env로 전달하지 않는다.

## Embedding profile 결정

이번 코드와 맞는 기본 이행안은 **Gemini profile로 staging corpus를 새 revision에 재색인하고 검증한 다음 활성화하는 것**이다. 기존 active revision은 staging 검증과 rollback 판단 전까지 보존한다. 운영 corpus를 직접 덮어쓰지 않는다.

기존 E5 revision이 진짜 `intfloat/multilingual-e5-small` 모델로 만들어졌는지 먼저 inventory와 ingest 기록으로 확인한다. `scripts/ingest_catalog_from_postgres.py`는 Gemini key가 없으면 deterministic hash backend로 fallback하면서 E5 profile ID를 쓸 수 있으므로, 그 경로의 E5 표시만으로 의미 임베딩이라고 판단하면 안 된다. 재색인 전에 명시적으로 Gemini key를 제공하고 `--hash-only`는 사용하지 않는다. 결과 revision의 `embedding_profile_id`가 `gemini-embedding-001-384@v1`인지, document/chunk/embedding 수가 일치하는지 확인한다.

Gemini API 비용·지연 또는 데이터 정책 때문에 E5를 유지하기로 결정한다면, 실제 고정 모델 artifact를 로드하고 profile identity를 검증하는 E5 `EmbeddingBackend`를 먼저 구현·테스트해야 한다. 현재 Plan/Execute에는 E5 backend가 없으므로 E5 유지 상태에서 dense route를 켜면 안 된다.

## `003_reviewed_facts.sql` 적용과 fact 검수

1. 변경이 검토·병합된 AI Engine release를 고정하고 staging DB backup/restore 절차를 확인한다.
2. 배포 artifact의 `migrations/ai/003_reviewed_facts.sql`을 `ONMARU_DB_AI_MIGRATION_USER`에 해당하는 별도 migration role로 staging DB에 한 번 적용한다. AI Engine runtime role을 migration에 사용하지 않는다.
3. migration owner로 실행 권한을 구성한다. runtime role 이름은 환경별 실제 role을 확인한 뒤 치환한다:

   ```sql
   GRANT USAGE ON SCHEMA ai TO <ai_runtime_role>;
   GRANT SELECT ON ai.reviewed_facts TO <ai_runtime_role>;
   ```

   이 표는 새 fact table에 필요한 최소 권한이다. corpus의 기존 테이블 권한은 별도 기존 권한 정책을 따른다.
4. 장소별 public source 자료를 사람이 검토해 사실 단위로 선별한다. 검색 chunk를 자동 승인하거나 모델이 만든 문장을 fact로 적재하지 않는다. 공개 계약의 `placeId`는 `ai.documents.source_id`와 같아야 한다. `chunk_id`, offset, 문장 원문은 active revision 문서와 정확히 일치해야 한다.
5. 승인된 fact는 감사 가능한 별도 적재 artifact로 준비하고 reviewer, 승인 시각, 출처 revision을 기록한다. 이 저장소에는 아직 정식 curated-fact 적재 CLI/seed가 없으므로, 임시 SQL을 운영에서 직접 실행하기 전에 적재 도구와 리뷰 절차를 PR로 추가한다.
6. 다음 확인 쿼리에서 불일치가 0건인지 확인하고, 승인 fact 수와 표본을 콘텐츠 담당자가 재검토한다:

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
4. 각 route에서 승인·제외·revocation 필터, grounding/evidence, timeout/fallback, 기존 board/state 보존, 로그상 corpus/profile/config version을 확인한다. 기능·품질·지연·메모리 결과를 기록한다.
5. 검증 결과를 BE와 AI Engine 양쪽 PR에 연결한다. 그 다음 별도 rollout 승인에 따라 staging flag부터 단계적으로 변경한다. 운영 flag는 staging 결과, rollback rehearsal, 배포 승인 전까지 false로 유지한다.

## 남은 blocker

- 구현은 [AI Engine PR #84](https://github.com/YRootLab/onmaru-ai-engine/pull/84)에 공유되어 있고 CI는 통과했다. PR은 현재 draft/open 상태이며 review와 merge가 남았다.
- production active corpus inventory와 embedding profile을 재확인해야 한다. 저장소 handoff에 남은 E5 정보는 이전 inventory 기록이다.
- curated fact 적재 도구, 실제 fact set, reviewer 승인·감사 절차가 아직 없다.
- PostgreSQL migration은 여기서 실행하지 않았다. runtime role grant도 실제 role명을 모르는 상태에서 적용하지 않았다.
- Spring 계약 테스트 통과는 live HTTP 합동 E2E 통과를 의미하지 않는다.
