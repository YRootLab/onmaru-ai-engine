# AI-RAG 문서 안내

이 디렉터리는 OnMaru AI Engine의 여정 검색·근거 생성·corpus·품질 평가 설계를 다룹니다. 이 문서는 주제별 문서 색인이며, 코드 상태를 대신 증명하지 않습니다. 운영 동작은 코드·migration·배포 digest·smoke 결과로 확인합니다.

## 먼저 확인할 문서

| 필요 내용 | 정본 |
|---|---|
| 제품 범위, 사용자 여정, 인수 조건, 활성화 평가 부록 | [PRD](prd.md) |
| 현재 출시 차단 요인과 구현/증거 격차 | [Production readiness gaps](production-readiness-gaps.md) |
| 요청에서 응답까지의 전체 모듈 경계 | [Module boundaries and pipelines](module-boundaries-and-pipelines.md) |
| 질문 처리, 검색 경로와 RAG 구조 | [Query processing](query-processing.md), [Architecture](architecture.md) |
| 운영·평가 실행 계획 | [Operations and evaluation](operations-and-evaluation.md) |
| 시스템 개요 시각 보고서 | [Generated system briefing](reports/2026-10-21-system-briefing.html) |

## 문서 주제별 색인

### 제품과 런타임 설계

- [PRD](prd.md): 제품 요구사항과 인수 기준. 여정 RAG 활성화 평가 부록은 후보 정책 호환, 서버 측 RAG gate, 비교 판정 및 배포 순서를 다룹니다.
- [Architecture](architecture.md): corpus 준비, 질의 실행, 검색·근거·생성 구성.
- [Module boundaries and pipelines](module-boundaries-and-pipelines.md): corpus, 온라인 여정 응답, 품질 감독의 책임과 입출력.
- [Request lifecycle](request-lifecycle.md): 요청 단계, Spring 승인 왕복, fallback과 오류 흐름.
- [Conversation and prompt design](conversation-and-prompt-design.md): 대화 UX와 작업별 prompt 설계.
- [Question understanding](question-understanding.md): 질의 표현, 동의어, 부정 및 복합 조건.
- [Query processing](query-processing.md): preprocessing, interpretation, search router와 검색 경로.

### API·데이터·보안 계약

- [Contracts and data](contracts-and-data.md): 요청/응답 및 대화 데이터 모델 설계.
- [Spring integration and SSE](spring-backend-integration-and-sse-architecture.md): Spring과 AI Engine 사이의 통합 설계.
- [Progress event contract](progress-event-contract.md): 진행 이벤트의 payload와 전달 경계.
- [Security and abuse](security-and-abuse.md): 입력·접근·출력 신뢰 경계와 오남용 방어.
- [Grounding and review](grounding-and-review.md): claim별 근거 검증 및 사람 검수 정책.
- [Observability contract](observability-contract.md), [Telemetry and harness schema](telemetry-and-harness-schema.md): 관측 필드, run artifact와 품질 harness 입력.

제품 공개 API, Spring 동작과 운영 데이터의 정본은 백엔드 저장소에 있습니다: [Spring AI-RAG 설계](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/ai-rag-spring/README.md), [공유 계약](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/contracts/README.md), [DB 문서](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/database/README.md).

### Corpus와 검색 인덱스

- [RAG storage schema](rag-storage-schema.md): AI schema의 revision, 문서, chunk, embedding 구조.
- [Corpus lifecycle and GC](corpus-lifecycle-and-gc.md): 활성/롤백 revision, 보존, 철회와 garbage collection.
- [Lexical search implementation](lexical-search-implementation.md): lexical 검색 구현 설계와 제한.
- [AWS ingestion guide](aws-ingestion-guide.md): 수집 환경 설정 및 실행 절차.
- [Operator read-only SQL](sql/README.md): 운영자가 실행할 AI schema embedding count 및 region distribution 집계.

### 평가·운영·품질 개선

- [Evaluation and environment tests](evaluation-and-environment-tests.md): gold set, 품질 지표, 부하·장애 검증.
- [Evaluation dataset provenance](evaluation-dataset-provenance.md): 데이터셋 출처·버전·재현성 기록.
- [Evaluation artifact index](../../evals/README.md): CLI 입력 v1.2와 현재 synthetic fixture가 실제 gold가 아님을 설명합니다.
- [Operations and evaluation](operations-and-evaluation.md): 운영 계측, 자원 측정 및 출시 gate.
- [Quality engineering agent](quality-engineering-agent.md), [Quality agent prompt contracts](quality-agent-prompt-contracts.md): 오프라인 진단·실험의 권한과 prompt 계약.
- [Production readiness gaps](production-readiness-gaps.md): 현재 구현, 검증 증거와 미완료 출시 조건을 구분합니다.

### 릴리스·이전·작업 추적

- [Deployment and release model](deployment-and-release-model.md): 이미지 발행, 승격 및 배포 소유 경계.
- [Repository split and monitoring](repository-split-and-monitoring.md): 저장소 이전과 관측 소유권.
- [v0.1.1 integration report](v0.1.1-spring-v0.3.54-integration-report.md), [v0.1.2 production wiring report](v0.1.2-production-wiring-and-spring-integration.md): 과거 버전별 기록. 현재 API/운영 상태의 정본으로 사용하지 않습니다.
- [Implementation issue plan](issue-planning/README.md): AI-RAG 하위 작업 분해와 GitHub Issue 연결.
- [Release evidence format](release-evidence/README.md): 검증 증거 artifact의 형식과 생성 방법.

## 시각 자료와 생성 산출물

- [`diagrams/`](diagrams/README.md): 다이어그램 원본과 재생성 방법. 그림은 목표 구조를 설명하며, 그 자체로 구현 상태를 나타내지 않습니다.
- [`reports/`](reports/): 생성된 HTML 보고서와 그 생성기. 원본 설계 문서를 수정한 뒤 생성기를 실행해 산출물을 갱신합니다.
- [`schemas/`](schemas/): 버전형 JSON Schema 등 기계 판독 계약.

기존 상대 경로는 링크 안정성을 위해 유지합니다. 새 문서는 위 주제 중 하나의 정본을 갱신하는 것을 우선하며, 별도 문서가 필요하면 이 색인에도 등록합니다.
