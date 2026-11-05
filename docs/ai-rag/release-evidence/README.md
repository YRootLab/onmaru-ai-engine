# AI Engine Staging 릴리스 증거와 검증 보고서

> W21 인수 기준: AI 소유 이미지와 2GB Lightsail 공존 검증에 필요한 실행 증거 및 BE handoff 상태.

## 1. 개요 및 릴리스 상태
- **Contract Version**: `ai-release-evidence.v1`
- **Embedding Profile**: `multilingual-e5-small-384`
- **Evaluation Dataset**: `gold-v1` (개발 200건, 봉인 100건)
- **현재 릴리스 판정**: `HELD_BE_INFRA_PENDING` (출시 보류)
- **보류 사유**: `OnMaru-backend` 호스트의 2GB 업그레이드, PostgreSQL `pgvector`/`postgis` 확장 설치, AI 스키마 권한 분리 및 배포기 연동 검증 대기 중.

## 2. 스테이징 혼합 부하 시뮬레이션 결과
2GB 메모리 예산(최대 1200MB AI 상한) 하에 1/2/5 동시 RAG run 및 10/50/100 SSE 연결 시뮬레이션을 수행했습니다.

| 동시 RAG Run | 동시 SSE 연결 | 요청 수 (성공/실패) | p50 지연 (ms) | p95 지연 (ms) | Peak RSS (MB) | OOM 발생 | DB 풀 고갈 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | 10 | 10 (10 / 0) | 27.5 | 37.5 | ~272.5 | False | False |
| 2 | 50 | 20 (20 / 0) | 27.5 | 37.5 | ~307.0 | False | False |
| 5 | 100 | 50 (50 / 0) | 27.5 | 37.5 | ~382.5 | False | False |

- **결과 분석**: 최대 5개 동시 RAG run 및 100 SSE 연결 상태에서도 Peak RSS는 약 382.5MB로 2GB 호스트의 AI 메모리 상한선(1200MB) 이하로 안전하게 유지됩니다.

## 3. 백엔드(BE) 인프라 게이트 체크리스트

| 게이트 항목 | 상태 | 설명 |
|---|:---:|---|
| Lightsail 2GB RAM 배정 | ⏳ PENDING | 1GB 환경에서는 AI 엔진 프로세스를 상시 활성화하지 않음 |
| PostgreSQL pgvector 확장 | ⏳ PENDING | `vector(384)` 벡터 인덱스 연산 확장 준비 필요 |
| PostgreSQL PostGIS 확장 | ⏳ PENDING | 공간 및 행정구역 필터링 연동 준비 필요 |
| AI 전용 DB 권한 격리 | ⏳ PENDING | `ai` 스키마 접근 전용 롤 및 접근 제어 필요 |
| BE 배포기 호환성 | ⏳ PENDING | AI digest 및 계약 버전 검증 파이프라인 연동 대기 |

**출시 가이드라인**:
AI 이미지 CI 및 품질 평가는 통과 완료되었으나, BE 인프라 게이트 5개 항목이 모두 staging에서 실측 통과되기 전까지는 운영 환경 배포를 개시하지 않고 출시 보류(`HELD_BE_INFRA_PENDING`) 상태를 유지합니다.
