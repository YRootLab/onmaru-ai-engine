# AWS Lightsail PostgreSQL AI RAG 데이터 적재 및 활성화 가이드

> 이 문서는 `OnMaruBE`에서 검증된 1,080건의 온마루 승인 장소 데이터셋(`data/seed/places_1080.json`)을 AWS Lightsail 상의 PostgreSQL `ai` 스키마로 적재하고, RAG 검색 서비스의 활성 코퍼스(`ai.active_corpus`)로 등록하는 운영 가이드입니다.

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

## 2. AWS Lightsail 서버 내 원클릭 적재 실행 방법

AI Engine 컨테이너와 PostgreSQL 컨테이너는 AWS Lightsail 내부 Docker 네트워크(`onmaru-lightsail_app`, `database`)에서 통신하므로, Lightsail 호스트에서 아래 명령을 실행합니다.

### 2.1. 서버 접속 후 실행

```bash
# 1. Lightsail 서버 접속
ssh -i <your-key.pem> ubuntu@<lightsail-host-ip>

# 2. OnMaru 인프라 디렉토리로 이동
cd /opt/onmaru/repo/infra/lightsail

# 3. 환경 변수 로드 (.env 파일 기준)
source .env

# 4. AI Engine 컨테이너 내부에서 데이터 적재 및 즉시 활성화 실행
docker compose --profile ai-engine exec ai-engine \
  python scripts/ingest_to_postgres.py \
    --input data/seed/places_1080.json \
    --dsn "postgresql://${ONMARU_DB_AI_MIGRATION_USER}:${ONMARU_DB_AI_MIGRATION_PASSWORD}@postgres:5432/${ONMARU_POSTGRES_DB}" \
    --activate
```

---

## 3. 적재 결과 검증 쿼리

적재가 정상적으로 완료되면 PostgreSQL에 접속하여 아래 쿼리로 활성 상태를 확인합니다.

```sql
-- 1. 활성 코퍼스 포인터 확인 (id=1, revision_id 일치 확인)
SELECT * FROM ai.active_corpus;

-- 2. 등록된 코퍼스 리비전 상태 확인 (state = 'ACTIVE' 또는 'VALIDATED')
SELECT revision_id, state, document_count, chunk_count, created_at 
FROM ai.corpus_revisions 
ORDER BY created_at DESC LIMIT 1;

-- 3. 적재된 문서 및 카테고리별 건수 확인 (총 1,080건)
SELECT category_code, COUNT(*) 
FROM ai.documents 
GROUP BY category_code 
ORDER BY COUNT(*) DESC;
```

---

## 4. 로컬 환경 테스트 (필요 시)

로컬에서 PostgreSQL 컨테이너를 띄우고 테스트할 경우:

```bash
uv run python scripts/ingest_to_postgres.py \
  --input data/seed/places_1080.json \
  --dsn "postgresql://onmaru_user:password@127.0.0.1:5432/onmaru" \
  --activate
```
