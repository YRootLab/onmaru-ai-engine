# AWS Lightsail PostgreSQL AI corpus 적재 가이드

> 현재 Plan/Execute의 staging 활성화는 [Plan/Execute staging runbook](../operations/plan-execute-staging-runbook.md)을 따른다. 이 문서는 JSON seed 기반 로컬/one-off 적재 경로를 설명하며, 운영 활성화 승인을 대신하지 않는다. 두 ingestion CLI는 Gemini profile로 새 revision을 stage만 하고, corpus activation은 별도 검증 CLI에서 수행한다.

---

## 1. 개요 및 데이터 규격

- **원본 데이터 소스**: `OnMaruBE/scripts/seed-reviews/all_hanoks_1080.json` (1,080건)
- **동기화 경로**: [`data/seed/places_1080.json`](file:///Users/yangseunghyeon/Development/OnMaru/OnMaru-AI-engine/data/seed/places_1080.json)
- **적재 대상 DB**: AWS Lightsail 인스턴스 내부의 PostgreSQL 17 (`ai` 스키마)
- **대상 테이블**:
  - `ai.corpus_revisions`: 코퍼스 개정 이력 및 메타데이터
  - `ai.documents`: 정규화된 공개 장소 문서 (1,080건)
  - `ai.chunks`: `SemanticChunker`로 분할된 검색 청크 (400~600 토큰)
  - `ai.active_corpus`: 단일 원자적 활성 코퍼스 포인터 (`id=1`)

### 카테고리 필터링 규칙 (100% 검증 통과)
온마루 표준 12개 카테고리 중 1,080건의 데이터는 다음 카테고리로 완벽하게 분류되어 적재됩니다:
- `HANOK` (한옥/고택)
- `HANOK_STAY` (한옥 숙박)
- `HANOK_CAFE` (한옥 카페/찻집)
- `HANOK_EXPERIENCE` (전통문화 체험)
- `HISTORIC_SITE` (고궁/유적지)
- `CULTURE_ART` (문화예술/박물관)
- `TRADITIONAL_FOOD` (향토음식)
- `LOCAL_SCENE` (체험마을)
- `LEISURE_ACTIVITY` (레저/야외)

---

## 2. Gemini profile로 새 revision stage

Gemini key는 보호된 secret 환경(`ONMARU_SECRET_GEMINI_API_KEY_CURRENT`)으로 one-off 작업에 주입한다. API key를 명령 인자로 전달하지 않는다. `--hash-only`는 `--dry-run`과 함께 사용할 때만 허용되며 실제 DB에는 쓸 수 없다.

### 2.1. 서버 접속 후 실행

```bash
# 1. Lightsail 서버 접속
ssh -i <your-key.pem> ubuntu@<lightsail-host-ip>

# 2. OnMaru 인프라 디렉토리로 이동
cd /opt/onmaru/repo/infra/lightsail

# 3. 환경 변수 로드 (.env 파일 기준)
source .env

# 4. 승인된 데이터 bundle을 Gemini profile로 stage (활성화하지 않음)
docker compose --profile ai-engine run --rm \
  -e ONMARU_AI_DB_DSN -e ONMARU_SECRET_GEMINI_API_KEY_CURRENT ai-engine \
  python scripts/ingest_to_postgres.py \
    --input data/seed/places_1080.json \
    --revision-id "$STAGING_GEMINI_REVISION"
```

one-off runner의 `ONMARU_AI_DB_DSN`과 `ONMARU_SECRET_GEMINI_API_KEY_CURRENT`에 writer DSN 및 Gemini key를 secret injection하고 `docker compose run -e` passthrough로 전달한다. 값을 CLI 인자나 Compose 상시 runtime 환경에 저장하지 않는다.

KTO active catalog에서 바로 가져오는 staging은 `scripts/ingest_catalog_from_postgres.py`를 사용하고, AI schema writer DSN과 catalog read DSN을 별도로 준다. 이 스크립트도 stage만 수행한다.

---

## 3. 적재 결과 검증 쿼리

적재가 정상적으로 완료되면 PostgreSQL에 접속하여 아래 쿼리로 활성 상태를 확인합니다.

```sql
-- 1. 활성 코퍼스 포인터 확인 (id=1, revision_id 일치 확인)
SELECT * FROM ai.active_corpus;

-- 2. 새 Gemini revision 상태와 embedding profile 확인
SELECT revision_id, state, embedding_profile_id, document_count, chunk_count,
       embedding_count, created_at
FROM ai.corpus_revisions 
ORDER BY created_at DESC LIMIT 1;

-- 3. 적재된 문서 및 카테고리별 건수 확인 (총 1,080건)
SELECT category_code, COUNT(*) 
FROM ai.documents 
GROUP BY category_code 
ORDER BY COUNT(*) DESC;
```

실제 count와 profile이 일치하고 staging 평가를 통과한 뒤 [별도 corpus activator](../operations/plan-execute-staging-runbook.md)에 같은 revision ID를 두 번 전달해 read-only 검증한다. 결과를 검토한 다음에만 `--apply`로 active pointer를 전환한다. 이 문서의 예시만으로 staging/운영 corpus를 활성화하지 않는다.

---

## 4. 로컬 환경 테스트 (필요 시)

로컬에서 PostgreSQL 컨테이너를 띄우고 테스트할 경우:

```bash
ONMARU_AI_DB_DSN="$AI_CORPUS_WRITE_DSN" \
ONMARU_SECRET_GEMINI_API_KEY_CURRENT="$GEMINI_KEY_FROM_SECRET_STORE" \
  uv run python scripts/ingest_to_postgres.py \
  --input data/seed/places_1080.json \
  --revision-id "rev-local-validation"
```
