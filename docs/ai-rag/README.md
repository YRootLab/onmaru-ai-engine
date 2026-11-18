# AI-RAG 문서 안내

이 디렉터리는 OnMaru AI Engine의 여정 검색·근거 생성·corpus·품질 평가 설계를 다룹니다. 이 문서는 주제별 문서 색인이며, 코드 상태를 대신 증명하지 않습니다. 운영 동작은 코드·migration·배포 digest·smoke 결과로 확인합니다.

## 먼저 확인할 문서

| 필요 내용 | 정본 |
|---|---|
| 제품 범위, 사용자 여정, 인수 조건 | [PRD](./product/prd.md) |
| 현재 역할 경계 판정, 카나리 분석, 우선 수정 게이트 | [2026-11-17 Canary role-boundary review](reports/2026-11-17-canary-role-boundary-review.md) |
| 현재 출시 차단 요인과 구현/증거 격차 | [Production readiness gaps](./operations/production-readiness-gaps.md) |
| 요청에서 응답까지의 전체 모듈 경계 | [Module boundaries and pipelines](./architecture/module-boundaries-and-pipelines.md) |
| 질문 처리, 검색 경로와 RAG 구조 | [Query processing](./architecture/query-processing.md), [Architecture](./architecture/architecture.md) |
| 운영·평가 실행 계획 | [Operations and evaluation](./operations/operations-and-evaluation.md) |
| 이전 목표 아키텍처 시각 스냅샷 | [2026-10-21 system briefing](reports/2026-10-21-system-briefing.html) |

## 현재 문서 기준

현재 역할 경계와 카나리에서 확인된 설계·구현 차이는 [2026-11-17 진단 보고서](reports/2026-11-17-canary-role-boundary-review.md)를 기준으로 읽습니다. 이 보고서는 제품 요구사항 전체를 대체하지 않습니다. [PRD](./product/prd.md)는 사용자 가치와 제품 인수 조건을 설명하고, 그 안의 과거 RAG 활성화 평가 부록은 재현성을 위한 레거시 기록입니다. 상세 목표 계약은 query-processing과 module-boundaries 문서에 있으며, 보고서와 충돌하면 카나리에서 확인된 현재 상태는 코드·배포 증거로, 목표 역할 경계는 최신 진단 보고서로 해석합니다.

2026-10-21 HTML은 당시 목표 아키텍처를 담은 생성 스냅샷입니다. 현재 구현이나 운영 카나리가 그 구조를 따른다는 증거로 사용하지 않습니다. 생성 HTML 내부의 설계 내용과 최신 진단의 차이는 최신 진단 보고서에서 확인할 수 있습니다.

## 문서 주제별 색인

### 제품

- [Conversation and prompt design](./product/conversation-and-prompt-design.md): 대화 UX와 작업별 prompt 설계.
- [PRD](./product/prd.md): 제품 요구사항과 인수 기준. 하단의 여정 RAG 활성화 평가 부록은 과거 `candidatePolicy`/후보 제한 운영 가정에 기반한 기록이며 현재 아키텍처의 구현 지시가 아닙니다.

### 아키텍처

- [Architecture](./architecture/architecture.md): corpus 준비, 질의 실행, 검색·근거·생성 구성.
- [Module boundaries and pipelines](./architecture/module-boundaries-and-pipelines.md): corpus, 온라인 여정 응답, 품질 감독의 책임과 입출력.
- [Query processing](./architecture/query-processing.md): preprocessing, interpretation, search router와 검색 경로.
- [Question understanding](./architecture/question-understanding.md): 질의 표현, 동의어, 부정 및 복합 조건.
- [Request lifecycle](./architecture/request-lifecycle.md): 요청 단계, Spring 승인 왕복, fallback과 오류 흐름.

### 통합 계약

- [Contracts and data](./integration/contracts-and-data.md): 요청/응답 및 대화 데이터 모델 설계.
- [Spring integration and SSE](./integration/spring-backend-integration-and-sse-architecture.md): Spring과 AI Engine 사이의 통합 설계.
- [Progress event contract](./integration/progress-event-contract.md): 진행 이벤트의 payload와 전달 경계.
- [Repository split and monitoring](./integration/repository-split-and-monitoring.md): 저장소 소유 경계와 관측 책임.

제품 공개 API, Spring 동작과 운영 데이터의 정본은 백엔드 저장소에 있습니다: [Spring AI-RAG 설계](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/ai-rag-spring/README.md), [공유 계약](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/contracts/README.md), [DB 문서](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/database/README.md).

### Corpus와 검색 인덱스

- [RAG storage schema](./data/rag-storage-schema.md): AI schema의 revision, 문서, chunk, embedding 구조.
- [Corpus lifecycle and GC](./data/corpus-lifecycle-and-gc.md): 활성/롤백 revision, 보존, 철회와 garbage collection.
- [Lexical search implementation](./data/lexical-search-implementation.md): lexical 검색 구현 설계와 제한.
- [AWS ingestion guide](./data/aws-ingestion-guide.md): 수집 환경 설정 및 실행 절차.
- [Operator read-only SQL](sql/README.md): 운영자가 실행할 AI schema embedding count 및 region distribution 집계.

### 데이터와 검색

- [AWS ingestion guide](./data/aws-ingestion-guide.md): 수집 환경 설정 및 실행 절차.
- [Corpus lifecycle and GC](./data/corpus-lifecycle-and-gc.md): 활성/롤백 revision, 보존, 철회와 garbage collection.
- [Lexical search implementation](./data/lexical-search-implementation.md): lexical 검색 구현 설계와 제한.
- [RAG storage schema](./data/rag-storage-schema.md): AI schema의 revision, 문서, chunk, embedding 구조.
- [Operator read-only SQL](sql/README.md): 운영자가 실행할 AI schema 집계.

### 품질과 평가

- [Evaluation and environment tests](./quality/evaluation-and-environment-tests.md): gold set, 품질 지표, 부하·장애 검증.
- [Evaluation dataset provenance](./quality/evaluation-dataset-provenance.md): 데이터셋 출처·버전·재현성 기록.
- [Evaluation artifact index](../../evals/README.md): CLI 입력 v1.2와 현재 synthetic fixture가 실제 gold가 아님을 설명합니다.
- [Grounding and review](./quality/grounding-and-review.md): claim별 근거 검증 및 사람 검수 정책.
- [Quality engineering agent](./quality/quality-engineering-agent.md), [Quality agent prompt contracts](./quality/quality-agent-prompt-contracts.md): 오프라인 진단·실험 권한과 prompt 계약.
- [Telemetry and harness schema](./quality/telemetry-and-harness-schema.md): 품질 harness 실행 artifact 계약.

### 운영과 보안

- [Deployment and release model](./operations/deployment-and-release-model.md): 이미지 발행, 승격 및 배포 소유 경계.
- [Observability contract](./operations/observability-contract.md): 운영 trace·metric 경계.
- [Operations and evaluation](./operations/operations-and-evaluation.md): 운영 계측, 자원 측정 및 출시 gate.
- [Production readiness gaps](./operations/production-readiness-gaps.md): 현재 구현, 검증 증거와 미완료 출시 조건.
- [Security and abuse](./operations/security-and-abuse.md): 입력·접근·출력 신뢰 경계와 오남용 방어.

### 계획과 이력

- [Implementation issue plan](issue-planning/README.md): AI-RAG 하위 작업 분해와 GitHub Issue 연결.
- [Release evidence format](release-evidence/README.md): 검증 증거 artifact의 형식과 생성 방법.
- [v0.1.1 integration report](./history/v0.1.1-spring-v0.3.54-integration-report.md), [v0.1.2 production wiring report](./history/v0.1.2-production-wiring-and-spring-integration.md): 이전 버전 기록. 현재 API/운영 상태의 정본으로 사용하지 않습니다.

## 시각 자료와 생성 산출물

- [`diagrams/`](diagrams/README.md): 다이어그램 원본과 재생성 방법. 그림은 목표 구조를 설명하며, 그 자체로 구현 상태를 나타내지 않습니다.
- [`reports/`](reports/): 생성된 HTML 스냅샷과 분석 보고서. 2026-10-21 HTML은 역사적 스냅샷이며, 최신 역할 경계 진단은 아래 Markdown 보고서가 정본입니다. 현재 빌더는 10월 파일을 덮어쓰므로, 새 시점의 HTML이 필요하면 출력 경로를 분리한 뒤 생성합니다.
- [2026-11-17 Canary role-boundary review](reports/2026-11-17-canary-role-boundary-review.md): 시스템 브리핑의 목표 파이프라인과 Spring 운영 카나리의 legacy 후보 제한 경로를 대조하고, 역할 오류·계약 불일치·출시 전 수정 게이트를 정리한 근거 기반 진단입니다.
- [2026-11-17 Canary role-boundary review · HTML](reports/2026-11-17-canary-role-boundary-review.html): 같은 진단의 읽기용 HTML. 위쪽에서 legacy 카나리 흐름과 목표 AI 소유 pipeline을 비교하고, 아래에 전체 보고서를 포함합니다.
- [보고서 목록](reports/README.md): 최신 HTML·Markdown 보고서와 과거 시스템 브리핑의 관계를 설명합니다.
- [`schemas/`](schemas/): 버전형 JSON Schema 등 기계 판독 계약.

새 문서는 위 주제 중 하나의 정본을 갱신하는 것을 우선하며, 별도 문서가 필요하면 이 색인에도 등록합니다. 자세한 [AI-RAG 문서 분류와 읽는 순서](DOCUMENTATION.md)를 참고하세요.
