# OnMaru AI Engine

OnMaru의 Python/FastAPI AI 엔진 저장소입니다. 자연어 질문 처리, 검색, 근거 기반 생성, 공개 corpus 색인, 비동기 품질 harness가 목표 범위입니다.

## Repository status

AI-RAG 설계 문서·다이어그램·HTML 보고서는 2026-10-22 이 저장소로 이전했습니다. 백엔드가 소유하는 문서 링크는 해당 변경의 검토·병합 후 불변 commit으로 고정할 예정입니다. FastAPI runtime은 백엔드의 기존 baseline을 이 저장소로 이동하는 중이며, AWS 운영 배포가 이전되었다는 뜻은 아닙니다.

정본 설계 진입점은 [`docs/ai-rag/README.md`](docs/ai-rag/README.md)입니다. 백엔드 저장소에는 짧은 진입 안내와 Spring 구현 계획만 남깁니다.

## Runtime and deployment boundary

AI 저장소는 검증된 FastAPI container image를 발행합니다. AWS credential, 운영 `.env`, PostgreSQL volume, Nginx, Lightsail host는 소유하지 않습니다. 기존 백엔드 저장소가 Lightsail Compose와 제한 배포 workflow를 소유합니다. 목표는 기존 Lightsail을 2GB로 확장한 뒤 Spring Boot, PostgreSQL, Nginx, FastAPI를 같은 인스턴스에서 실행하는 것이며 두 번째 인스턴스는 계획하지 않았습니다.

Plan/Execute의 Postgres corpus, lexical/vector 검색, reviewed-fact grounding 코드는 [PR #84](https://github.com/YRootLab/onmaru-ai-engine/pull/84)에서 검토 중이며 아직 운영 배포된 상태가 아닙니다. PR merge 뒤에도 staging profile 재색인, migration/fact 준비, Spring live HTTP E2E 전까지 Spring flag는 false로 유지합니다. 구체적인 배선과 순서는 [Plan/Execute staging runbook](docs/ai-rag/operations/plan-execute-staging-runbook.md)을 기준으로 합니다.

The private two-step plan/execute boundary is documented in
[`src/onmaru_ai/api/README.md`](src/onmaru_ai/api/README.md). It uses the W0
contracts. The default application (`onmaru_ai.main:app`) wires the production
planner and executor through `create_production_plan_execute_service`; set
`ONMARU_DISABLE_DEFAULT_PLAN_EXECUTE=true` to return 503 instead.

## 운영 설정과 RAG/LLM 활성화

운영 컨테이너의 기본값은 `ONMARU_RAG_ENABLED=false`, `ONMARU_JOURNEY_GEMINI_ENABLED=false`입니다. 아래 표는 2026-11-11 legacy `/proposals` 및 `/stream` 경로 기준이며, Plan/Execute 배포 상태는 위 staging runbook을 확인하세요. Plan/Execute feature flag도 합동 staging 검증 전까지 false입니다.

### 현재 동작 요약

| 플래그 / 설정 | 기본값 | 실제 효과 |
| :--- | :--- | :--- |
| `ONMARU_RAG_ENABLED` | `false` | 레거시 `/internal/v1/journey/proposals`의 `useRag` 경로만 제어합니다. Plan/Execute의 feature flag와 별개입니다. |
| `ONMARU_JOURNEY_GEMINI_ENABLED` | `false` | 레거시 제안 경로와 `/stream`에서만 Gemini를 호출합니다. plan/execute의 근거·제안 생성에는 관여하지 않습니다. |
| `ONMARU_GEMINI_MODEL_NAME` | `gemini-2.5-flash` | 위 Gemini 호출의 모델 이름입니다. |
| `ONMARU_SECRET_GEMINI_API_KEY_CURRENT` | 시작 시 필수 | 플래그와 무관하게 시작 시 검증됩니다. |
| `ONMARU_SPRING_BASE_URL` | 미설정 시 `http://staging-api:8080` | 운영에서는 Spring 내부 origin을 명시하세요. 미설정이어도 `/ready`는 통과합니다. |

staging Compose 파일은 이 저장소에 없습니다. 백엔드 저장소의 Lightsail Compose가 소유합니다. 그 파일에서 RAG를 `false`로 고정한 경우, 값만 `true`로 바꾸면 위 표에 따라 효과가 없습니다.

### RAG를 실제로 켜기 위해 필요한 조건

1. 이 조건은 legacy `ONMARU_RAG_ENABLED` 경로에만 해당합니다. Plan/Execute는 별도 구조와 staging gate를 사용합니다.
2. Plan/Execute retrieval 및 생성 조건은 [staging runbook](docs/ai-rag/operations/plan-execute-staging-runbook.md)을 따릅니다.
3. Corpus revision은 Gemini profile로 stage·검증하고, 검증한 뒤 별도 activator로 활성화해야 합니다.
4. 평가 보고서(`RagActivationPolicy.evaluate`)가 전체 통과하고, 기준선 대비 `retrievalRecallAt5`·`ndcgAt3`·`claimSupport` 중 하나 이상이 양의 개선을 보이며, 지연·비용이 악화되지 않아야 `enabled` 기록이 남습니다.
5. 요청은 `useRag=true`만 보내면 됩니다. 활성 corpus revision은 AI 서버가 선택하고, 실제 사용한 `corpusRevisionId`를 응답에 반환합니다. 요청의 기존 `corpusRevisionId`는 호환을 위해 받을 수 있지만 선택에는 사용하지 않습니다.
6. Plan/Execute query embedding은 `gemini-embedding-001-384@v1`이며 active revision profile과 일치해야 합니다. 두 corpus ingestion CLI는 Gemini key가 없으면 실패합니다. `--hash-only --dry-run`은 local-only profile이며 staging corpus를 만들지 않습니다.

### Gemini 근거 생성을 켜기 전에

- 레거시 제안 경로만 Gemini를 씁니다. 응답은 `candidateRefs` 안의 ID만 허용합니다.
- Plan/Execute의 claim generation은 exact reviewed facts와 source span을 검사한 뒤 Gemini를 호출합니다. staging에서 `003_reviewed_facts.sql` 적용과 검수 fact 적재가 끝나기 전에는 grounded generation을 운영에서 켜지 않습니다.
- 고정 fixture 기준의 claim→evidence→place 연결 검증은 `tests/generation/test_grounded_contract_fixtures.py`가 CI에서 수행합니다.

### pgvector 점검 SQL (운영 DB, AI migration 소유자 계정으로 실행)

```sql
-- 1) 확장 설치 여부
SELECT extname, extversion FROM pg_extension WHERE extname IN ('vector', 'pg_trgm');

-- 2) 임베딩 컬럼 타입: 기대값 vector(384)
SELECT format_type(atttypid, atttypmod) AS embedding_type
FROM pg_attribute
WHERE attrelid = 'ai.embeddings'::regclass AND attname = 'embedding' AND NOT attisdropped;

-- 3) active revision과 상태: state는 ACTIVE여야 합니다
SELECT a.revision_id, r.state, r.embedding_profile_id, r.document_count,
       r.chunk_count, r.embedding_count, r.activated_at
FROM ai.active_corpus a
LEFT JOIN ai.corpus_revisions r ON r.revision_id = a.revision_id
WHERE a.id = 1;

-- 4) active revision의 실제 차원: 기대값 384 한 종류만 나와야 합니다
SELECT vector_dims(e.embedding) AS dims, count(*) AS rows
FROM ai.embeddings e
WHERE e.revision_id = (SELECT revision_id FROM ai.active_corpus WHERE id = 1)
GROUP BY 1;

-- 5) 장소·청크·임베딩 수 (active revision)
SELECT
  (SELECT count(DISTINCT d.place_id) FROM ai.documents d
     WHERE d.revision_id = a.revision_id) AS places,
  (SELECT count(*) FROM ai.chunks c WHERE c.revision_id = a.revision_id) AS chunks,
  (SELECT count(*) FROM ai.embeddings e WHERE e.revision_id = a.revision_id) AS embeddings
FROM ai.active_corpus a
WHERE a.id = 1;
```

## 개발 환경

Python 3.12와 `uv`를 사용합니다.

```bash
uv sync --frozen --all-groups
uv run pytest
uv run ruff check
uv run mypy
uv run uvicorn onmaru_ai.main:app --reload --port 8001
```

Offline AI 평가:

```bash
uv run python scripts/run-ai-evals \
  --input evals/journey-eval-contract-fixture-v1.json \
  --output /tmp/onmaru-ai-eval-report.json
```

`evals/journey-eval-contract-fixture-v1.json`은 CLI 계약을 확인하는 4건의 synthetic fixture이며, 활성화 판단용 gold dataset이 아닙니다. 평가 입력 v1.2는 고정 질문·지역·후보 순서와 전체 image digest, embedding profile 및 threshold를 요구합니다. [평가 artifact 안내](evals/README.md)를 참고하세요.
