# OnMaru AI Engine

OnMaru의 Python/FastAPI AI 엔진 저장소입니다. 자연어 질문 처리, 검색, 근거 기반 생성, 공개 corpus 색인, 비동기 품질 harness가 목표 범위입니다.

## Repository status

AI-RAG 설계 문서·다이어그램·HTML 보고서는 2026-10-22 이 저장소로 이전했습니다. 백엔드가 소유하는 문서 링크는 해당 변경의 검토·병합 후 불변 commit으로 고정할 예정입니다. FastAPI runtime은 백엔드의 기존 baseline을 이 저장소로 이동하는 중이며, AWS 운영 배포가 이전되었다는 뜻은 아닙니다.

정본 설계 진입점은 [`docs/ai-rag/README.md`](docs/ai-rag/README.md)입니다. 백엔드 저장소에는 짧은 진입 안내와 Spring 구현 계획만 남깁니다.

## Runtime and deployment boundary

AI 저장소는 검증된 FastAPI container image를 발행합니다. AWS credential, 운영 `.env`, PostgreSQL volume, Nginx, Lightsail host는 소유하지 않습니다. 기존 백엔드 저장소가 Lightsail Compose와 제한 배포 workflow를 소유합니다. 목표는 기존 Lightsail을 2GB로 확장한 뒤 Spring Boot, PostgreSQL, Nginx, FastAPI를 같은 인스턴스에서 실행하는 것이며 두 번째 인스턴스는 계획하지 않았습니다.

현재 이동 중인 FastAPI 코드는 기존 16차원 결정적 임베딩·메모리 검색 baseline입니다. 이 코드를 384차원 pgvector, BM25, hybrid ranking이 구현된 것으로 간주하지 않습니다. 실제 운영 배포 전에는 코드·DB migration·독립 CI·digest 기반 배포 및 공존 검증이 필요합니다. 자세한 목표는 [배포/릴리스 설계](docs/ai-rag/deployment-and-release-model.md)를 참고하세요.

The private two-step plan/execute boundary is documented in
[`src/onmaru_ai/api/README.md`](src/onmaru_ai/api/README.md). It uses the W0
contracts. The default application (`onmaru_ai.main:app`) wires the production
planner and executor through `create_production_plan_execute_service`; set
`ONMARU_DISABLE_DEFAULT_PLAN_EXECUTE=true` to return 503 instead.

## 운영 설정과 RAG/LLM 활성화

운영 컨테이너의 기본값은 `ONMARU_RAG_ENABLED=false`, `ONMARU_JOURNEY_GEMINI_ENABLED=false`입니다. 두 플래그를 바꾸기 전에 아래 현재 동작을 확인하세요. 2026-11-11 코드 기준으로 **플래그만 켜서는 RAG 검색이 실행되지 않습니다.**

### 현재 동작 요약

| 플래그 / 설정 | 기본값 | 실제 효과 |
| :--- | :--- | :--- |
| `ONMARU_RAG_ENABLED` | `false` | 레거시 `/internal/v1/journey/proposals`의 `useRag` 경로에서만 읽습니다. `create_app`이 `rag_retriever`와 `InMemoryRagActivationLog`를 주입하지 않으므로 `true`여도 근거는 `[]`입니다. plan/execute는 읽지 않습니다. |
| `ONMARU_JOURNEY_GEMINI_ENABLED` | `false` | 레거시 제안 경로와 `/stream`에서만 Gemini를 호출합니다. plan/execute의 근거·제안 생성에는 관여하지 않습니다. |
| `ONMARU_GEMINI_MODEL_NAME` | `gemini-2.5-flash` | 위 Gemini 호출의 모델 이름입니다. |
| `ONMARU_SECRET_GEMINI_API_KEY_CURRENT` | 시작 시 필수 | 플래그와 무관하게 시작 시 검증됩니다. |
| `ONMARU_SPRING_BASE_URL` | 미설정 시 `http://staging-api:8080` | 운영에서는 Spring 내부 origin을 명시하세요. 미설정이어도 `/ready`는 통과합니다. |

staging Compose 파일은 이 저장소에 없습니다. 백엔드 저장소의 Lightsail Compose가 소유합니다. 그 파일에서 RAG를 `false`로 고정한 경우, 값만 `true`로 바꾸면 위 표에 따라 효과가 없습니다.

### RAG를 실제로 켜기 위해 필요한 조건

1. 활성화 기록을 영속 저장소에 남기도록 `InMemoryRagActivationLog`를 교체하고, `RagEvidenceRetriever`(pgvector 검색)를 `create_app`에 주입해야 합니다. 현재 둘 다 없습니다.
2. 검색 라우트의 lexical·dense searcher를 `HybridRetrievalCoordinator`에 연결해야 합니다. 현재 후보는 항상 0개입니다.
3. 코퍼스 revision을 `ai.corpus_revisions`에 `ACTIVE`로 적재하고 `ai.active_corpus.revision_id`로 가리켜야 합니다.
4. 평가 보고서(`RagActivationPolicy.evaluate`)가 전체 통과하고, 기준선 대비 `retrievalRecallAt5`·`ndcgAt3`·`claimSupport` 중 하나 이상이 양의 개선을 보이며, 지연·비용이 악화되지 않아야 `enabled` 기록이 남습니다.
5. 요청의 `useRag=true`와 `corpusRevisionId`가 함께 와야 합니다. 빠지면 422입니다.
6. 임베딩은 `e5-small-384` 프로필이고 차원은 384여야 합니다. 현재 적재 스크립트의 `DeterministicHashBackend`는 의미 임베딩이 아닙니다. 의미 검색을 켜기 전에 실제 임베딩 모델로 다시 적재해야 합니다.

### Gemini 근거 생성을 켜기 전에

- 레거시 제안 경로만 Gemini를 씁니다. 응답은 `candidateRefs` 안의 ID만 허용합니다.
- plan/execute의 근거 생성은 Gemini를 쓰지 않습니다. `generation/EvidenceGenerator`는 검증된 사실 목록(`verifiedFacts`)과 근거 span을 요구하며, 운영 경로에 아직 연결되지 않았습니다.
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
  --input evals/journey-held-out-v1.json \
  --output /tmp/onmaru-ai-eval-report.json
```
