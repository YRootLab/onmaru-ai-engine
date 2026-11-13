# AI Engine 릴리스 evidence 상태

> 이 디렉터리의 현재 JSON은 실제 staging 계측 결과가 아닙니다. 생성 도구가 만드는 synthetic reference load 수치이며 릴리스 승인 근거로 사용할 수 없습니다.

## 현재 evidence

- Contract: `ai-release-evidence.v2`
- Measurement mode: `SIMULATED_REFERENCE_ONLY`
- 판정: 인프라 gate 확인 여부와 관계없이 실측 결과가 없어 release hold 상태입니다.
- 합성 데이터에는 컨테이너 실행, DB 연결, 검색, RSS, latency 측정이 포함되지 않습니다.
- `generate_release_evidence`는 측정된 host/DB 상태를 확인하지 않습니다. `STAGING_*` 환경 변수는 checklist 예시를 채울 뿐 실제 운영 확인 증거가 아닙니다.

다음 표는 scenario 형식을 보여주기 위한 추정치입니다. 실제 용량·지연의 증거가 아닙니다.

| 동시 RAG Run | 동시 SSE 연결 | 합성 요청 수 | 합성 p50 지연 (ms) | 합성 p95 지연 (ms) | 추정 RSS (MB) | OOM/DB |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 10 | 10 | 27.5 | 37.5 | 272.5 | 합성 기본값 |
| 2 | 50 | 20 | 27.5 | 37.5 | 307.0 | 합성 기본값 |
| 5 | 100 | 50 | 27.5 | 37.5 | 382.5 | 합성 기본값 |

## 인프라 확인 목록

| 게이트 항목 | 상태 | 설명 |
|---|:---:|---|
| Lightsail 2GB RAM 배정 | ⏳ PENDING | 1GB 환경에서는 AI 엔진 프로세스를 상시 활성화하지 않음 |
| PostgreSQL pgvector 확장 | ⏳ PENDING | `vector(384)` 벡터 인덱스 연산 확장 준비 필요 |
| PostgreSQL PostGIS 확장 | ⏳ PENDING | 공간 및 행정구역 필터링 연동 준비 필요 |
| AI 전용 DB 권한 격리 | ⏳ PENDING | `ai` 스키마 접근 전용 롤 및 접근 제어 필요 |
| BE 배포기 호환성 | ⏳ PENDING | AI digest 및 계약 버전 검증 파이프라인 연동 대기 |

## 실제 측정 결과 제출

릴리스 판단용 evidence에는 immutable AI image digest, corpus/dataset hash, 환경·컨테이너 제한, 실행 시각·반복 횟수·동시성, 실제 RSS/지연/오류/DB pool 결과와 기존 API 영향이 포함되어야 합니다. 512MB 적재·검색 측정과 2GB 혼합 부하는 실제 staging/container 실행에서 별도로 수집하세요. 모두 수집되기 전에는 RAG 활성화 또는 release approval을 기록하지 않습니다.
