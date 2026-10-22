# AI 저장소 분리와 관측 운영 결정

> 상태: 2026-10-22 문서 이전 review branch 게시. AI-RAG 설계 문서는 [`docs/ai-rag-transfer`](https://github.com/YRootLab/onmaru-ai-engine/tree/docs/ai-rag-transfer/docs/ai-rag) branch에 복사됐고 기본 브랜치 병합 전이다. FastAPI 코드·배포 경로는 이전되지 않았다. AI-RAG 정본은 이 review branch가 기본 브랜치에 병합된 뒤 해당 저장소가 된다. 백엔드 저장소에는 Spring 구현·연동 계획과 계약을 유지한다. 이 문서는 현재 운영 계측 완료를 주장하지 않는다.

## 1. 저장소와 정본 소유권

`OnMaru-backend`는 Spring 업무 API·회원 대화·공개 장소·SQL·SSE·최종 검증·운영 배포를 소유한다. `onmaru-ai-engine`은 FastAPI 비공개 API·질문 해석/route 제안·AI 코퍼스·임베딩·검색·근거 제한 생성·오프라인 평가와 `onmaru_ai.quality_harness`를 소유한다. 별도 Git 저장소가 되어도 같은 2GB Lightsail 호스트의 비공개 네트워크와 PostgreSQL `ai` 스키마를 사용할 수 있으며, AI에 Spring 업무 스키마의 쓰기 권한을 주지 않는다. 레포 분리는 별도 상시 worker 또는 추가 인스턴스의 근거가 아니다.

| 문서·계약 | 이전 후 정본 | 이유·전환 방법 |
|---|---|---|
| 제품 PRD와 AI 사용자 경험, 대화 흐름·프롬프트, 질문 처리·검색 설계, AI 요청 생명주기·안전 정책 | AI `docs/ai-rag/` | AI 기능의 요구사항과 엔진 구현을 같은 PR에서 갱신한다. Spring이 소유하는 공개 API·회원 대화 확정 계약은 BE `docs/ai-rag-spring/` 및 `docs/contracts/`에서 관리한다. |
| AI 데이터·검색·생성 아키텍처, RAG 저장 스키마, corpus 수명/GC, 근거 검증, AI 평가·환경 실험, 품질 harness, AI 모듈 구조·도식·통합 보고서 | AI `docs/ai-rag/` | 전체 AI-RAG 설계의 정본으로 함께 이전한다. 이전 후 보고서 빌더는 같은 저장소의 AI 문서를 포함하고, BE 소유 계약은 버전이 고정된 링크로 참조한다. 중복 Markdown 정본은 두지 않는다. |
| Spring과 AI 간 시스템 경계·통합 observability 계약 | BE `docs/ai-rag-spring/` 및 `docs/contracts/` | 각 서비스의 계측 세부사항은 각 저장소가 소유하고, `traceparent`, 공통 run 식별자, span/metric 이름 등 상호운용 계약과 통합 검증 절차는 BE에 둔다. AI 저장소 문서에서는 이 문서를 버전 고정 링크로 참조한다. |
| 내부 OpenAPI/JSON Schema·호환 fixture | BE `docs/contracts/` | 공개 API와 Spring→AI envelope의 발행 정본을 한 곳에 둔다. AI CI는 고정 BE commit의 계약을 읽어 consumer test를 실행하고, BE CI는 AI 이미지/fixture의 호환 버전을 시험한다. 서로 독립적으로 같은 schema를 편집하지 않는다. |
| Spring 소유 품질 관측/공개 상태 MCP adapter | BE docs/ai-rag-spring/와 docs/contracts/mcp/ | Spring은 Spring 사실의 MCP read-only endpoint·인가를 소유하고, AI Engine은 MCP client 및 Python 내부 tool registry를 소유한다. 공유 tool catalog는 BE docs/contracts/mcp/quality-tools.v1.json 하나를 발행 정본으로 삼는다. ADR-0018은 제안 상태이며 endpoint 구현은 별도 승인/검증 전까지 추가하지 않는다. |
| Spring↔FastAPI orchestration 및 정형 조회 | BE `docs/ai-rag-spring/journey-query-mcp.md`와 ADR-0019 제안 | plan/execute는 private REST를 기준선으로 구현·계측하고, 이 hop이 병목일 때 gRPC unary를 동일 계약으로 비교한다. `PlaceQueryPort`는 Spring 소유의 별도 typed 조회 경계이며 MCP는 tool discovery가 필요한 경우에만 쓴다. BM25/vector retrieval은 AI 레포 내부에 남는다. |
| 품질 조사 system prompt·격리 runner | AI `docs/ai-rag/`와 코드 | prompt version/hash, schema validator, Python tool registry, sandbox runner와 실행 제약은 실제 구현과 같은 저장소에서 갱신한다. Spring이 제공하는 도구의 권한·인가·응답 스키마는 BE MCP 계약으로 분리한다. |
| 현행 FastAPI 코드·테스트·`evals/`·`pyproject.toml`·`uv.lock`·Dockerfile | AI 저장소 루트 | 기존 `ai/`에서 이전한다. 기존 `evals/`를 `quality_harness` 구현 완료로 간주하거나 이름만 바꾸지 않는다. |
| SSAFY 요구사항 PDF | 원래 승인된 보관 위치 | PDF에 `對外秘`가 표시돼 있다. 공개 AI 레포·README·생성 HTML·CI artifact에 복사하지 않는다. 과제 재사용·제출 범위는 담당 교수·코치 안내를 확인한다. |

BE의 `docs/ai-rag/README.md`는 AI 정본으로 가는 안내 문서로 전환했다. AI 문서 이전 PR을 병합한 뒤에는 AI 저장소의 `docs/ai-rag/README.md`를 정본 진입점으로 사용한다. **두 저장소에 동일한 Markdown을 복제해 각각 수정하지 않는다.** 보고서 빌더는 AI 소유 문서만 본문으로 묶으며, BE 소유 계약은 고정 링크로 연결한다. BE 전용 구현 항목은 `docs/ai-rag-spring/` 및 `docs/contracts/`에 구현 인수 기준과 검증 방법을 유지한다. 코드·운영 배포 이전은 별도의 호환성 gate를 통과한 뒤 진행한다.

## 2. 저장소 분리와 단일 Lightsail 배포

Git 저장소와 실행 인스턴스는 별개의 경계다. FastAPI 코드를 `onmaru-ai-engine`으로 옮겨도 새 AWS 인스턴스를 만들지 않는다. 현재 Lightsail Compose, Nginx, PostgreSQL volume, Blue-Green Spring 배포와 제한 SSH deployer는 백엔드 저장소가 계속 소유하고, AI 저장소는 검증된 FastAPI 컨테이너 이미지를 GHCR에 발행한다. AI Engine은 기존 Lightsail을 2GB 플랜으로 확장하고 같은 Docker host의 비공개 network에서 실행하는 목표다. 현재 운영 배포에는 FastAPI가 아직 포함되지 않았으므로 실제 공존은 출시 전 검증 과제다.

| 책임 | 정본 저장소 | 경계 |
|---|---|---|
| FastAPI 코드·Python 의존성·테스트·AI 전용 CI와 immutable image | `onmaru-ai-engine` | OCI image를 GHCR에 SHA/digest로 발행한다. 운영 호스트·SSH 키·운영 `.env`를 저장하지 않는다. |
| Lightsail Compose·Nginx·DB image/volume·host resource limit·제한 배포기 | `OnMaru-backend` | 기존 인스턴스와 운영 volume을 유지한다. `ai-engine` 서비스는 외부 포트를 publish하지 않고 Spring/PostgreSQL의 사설 Docker network에만 연결한다. |
| 서비스 간 release pairing·contract compatibility·운영 승격/rollback | `OnMaru-backend` 배포 workflow와 계약 문서 | 배포 입력은 Spring SHA/digest와 AI digest를 명시적으로 고정한다. 각 이미지 CI는 분리하되 운영 승격은 호환 가능한 두 artifact 조합만 허용한다. |
| AI 데이터 스키마 정의 | AI 스키마는 AI 문서/코드에서 제안·migration 관리, host DB/백업/권한 실행은 BE 운영이 관리 | AI 런타임에는 `ai` 스키마 전용 최소 권한만 부여한다. migration 실행 identity는 런타임과 분리하고 승인된 배포 gate에서 수행한다. Spring 업무 schema의 쓰기 권한과 PostgreSQL 외부 포트는 주지 않는다. |

배포 원칙은 다음과 같다.

1. 기존 Lightsail 인스턴스의 플랜을 2GB로 올린 뒤 Spring·PostgreSQL/PostGIS/pgvector·Nginx·FastAPI·CPU 임베딩/reranker가 한 호스트에서 공존하는지 측정한다. 업그레이드 전에는 AI 컨테이너를 운영에 올리지 않는다.
2. DB와 Nginx는 기존 Compose 프로젝트·named volume·백업 절차를 유지한다. FastAPI는 별도 저장소에서 빌드한 immutable GHCR digest를 `.env` 또는 제한된 release manifest로 전달한다. `latest` tag로 운영 배포하지 않는다.
3. Spring Blue-Green 두 슬롯은 기존 메모리 상한 안에서 배포한다. FastAPI는 2GB 측정 전까지 Blue-Green 복제하지 않고 단일 서비스로 운영한다. FastAPI 교체 중 RAG 요청은 시간 제한된 fallback/error 정책을 타고 Spring의 나머지 기능은 계속 제공한다.
4. AI digest 교체는 health/readiness, contract version, DB migration 상태를 확인한다. 실패하면 이전 AI digest로 되돌린다. AI 모델이나 retriever가 메모리에 올라오는 상태에서 후보 컨테이너를 중복 기동하지 않으며, 배포 시 RSS·MemAvailable·swap·CPU를 확인한다.
5. corpus embedding/대량 인덱싱은 온라인 요청과 분리된 제한 concurrency·낮은 CPU 우선순위의 작업으로 시작한다. 전용 worker를 상시 두지 않는다. 메모리/지연 budget을 넘거나 복구 시간이 길면 운영 용량/작업 방식을 먼저 조정한다.

현재 [Lightsail runbook](https://github.com/YRootLab/OnMaru-backend/blob/develop/infra/lightsail/README.md)은 FastAPI 운영 배포를 별도 Lightsail로 미루는 과거 기준 문장이 있다. AI 기능을 같은 인스턴스에 도입하기 전 해당 문장과 배포 workflow/deployer 인자를 새 계약에 맞춰 갱신하고, Spring 단독 운영 경로를 깨지 않는 compose·rollback 검증을 추가한다. 상세 구현 항목은 [Spring 저장소/배포 통합 계획](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/ai-rag-spring/repository-and-deployment.md)에 둔다.

### 이전 및 배포 호환성 게이트

1. AI 레포에서 독립 `uv sync --frozen`, lint/typecheck/pytest, 평가 fixture, Docker build를 통과한다. 이미지에는 source SHA·계약 버전을 붙인다.
2. BE의 `ai/` 경로를 가리키는 CI·Docker·배포 job을 열거하고, 새 AI 이미지 digest를 같은 Lightsail Compose 배포 입력으로 바꾼다. 비공개 내부 주소, 인증, TLS, DB 최소 권한을 2GB staging에서 검증한다.
3. Spring의 내부 요청과 FastAPI 응답은 `contractVersion`, 허용 corpus/config, deadline, 오류 코드를 고정한다. N/N-1 호환 또는 순차 전환 가능 범위를 계약 fixture로 입증한다.
4. staging에서 정상·timeout·불일치·rollback·SSE 재접속과 같은 trace의 부모/자식 span을 확인한다. 새 AI 이미지와 기존 Spring 이미지의 호환성을 확인하기 전 운영 트래픽을 전환하지 않는다.
5. 전환 뒤에만 BE `ai/`와 옛 CI 경로를 제거한다. 새 AI 저장소가 비거나 같은 호스트 배포·복구가 미검증이면 현재 경로를 유지한다.

## 3. 관측 백엔드와 전송 경로

**Grafana Cloud를 통합 조회·경보 백엔드로 채택**한다. 기존 Prometheus 호환 metrics 경로와 Grafana dashboard/alert를 재사용하고, 두 앱의 trace는 같은 Grafana Cloud stack으로 보낸다. Prometheus는 집계 metric을 다루며 개별 분산 trace 저장소로 취급하지 않는다. 별도 Tempo·Loki·Prometheus·Langfuse 서버를 2GB Lightsail에 상주시켜 시작하지 않는다. Grafana Cloud의 [OTLP 직접 전송](https://grafana.com/docs/grafana-cloud/send-data/otlp/send-data-otlp/)은 가능하지만 Collector보다 재시도·필터·표본화 제어가 약하므로 bounded exporter와 유실 metric을 조건으로 둔다. 실제 stack의 traces 조회·인증·상품 한도는 staging에서 확인한다.

| 신호 | 첫 경로 | 정본·실패 시 동작 |
|---|---|---|
| Metrics | 기존 `/actuator/prometheus` 수집이 운영에서 유효하면 유지하고 AI metric을 같은 Prometheus 호환 경로에 연결한다. 유효하지 않으면 두 앱의 OTLP metrics로 **한 경로만** 선택한다. | Grafana 대시보드·경보. scrape와 OTLP 중복 수집 금지. 집계 metric은 trace sampling과 무관하게 수집한다. |
| Traces | Spring Micrometer/OTel과 FastAPI OTel SDK → Grafana Cloud OTLP traces. 초기에는 앱에서 직접 전송한다. | 단계별 진단 자료. export 오류·429·유실은 사용자 답변을 막지 않으며 유실 건수와 coverage를 별도 기록한다. |
| Logs | 기존 구조화 애플리케이션 로그에 허용된 `traceId`, `spanId`, `runId`, 단계/오류 코드를 연결한다. | 운영 로그는 현행 수집·보존 경로를 먼저 확인한다. 새 Loki나 원문·prompt 본문 수집은 시작 조건이 아니다. |
| 재현·감사 | `QualityReviewItem`, 평가 artifact hash, 비용·철회·사용량 ledger는 각 소유 DB/접근 제한 저장소 | 샘플링되거나 만료된 trace를 정답 기록으로 삼지 않는다. 일반 품질 검토 큐는 최초 생성부터 최대 3개월. |

Spring HTTP client가 **현재 활성 span context**를 W3C `traceparent`로 주입하고 FastAPI가 원격 parent context를 추출해 자식 server span을 시작해야 한다. `traceId` 문자열만 같거나 수동으로 올제로 `parent-id`를 만드는 것은 연결된 trace가 아니다. 현재 `InternalAiRequestHeadersFactory`의 `0000000000000000` parent ID와 FastAPI `correlation.py`의 문자열 추출은 수정·통합 검증 대상이다. Spring async executor·SSE 재연결은 업무 `runId`로 상관관계를 유지하되, 재연결을 원래 HTTP 요청의 무한 연장 span으로 만들지 않는다. 비동기 corpus sync와 품질 실험은 각자 새 root trace로 기록하고 원래 요청과는 artifact의 `runId`/trace reference로 연결한다.

초기 pilot에서는 AI run의 span을 100% 전송해 연결·누락을 확인하되, **영구 수집률이나 무료 보장을 약속하지 않는다.** 전송량·Grafana Cloud 사용량·무료 한도·2GB RSS/지연을 실측하고 표본 비율을 조정한다. trace가 표본에서 빠져도 run 총수·실패수·지연 histogram과 영속 평가 artifact가 남아야 한다. 원문 질문, 회원 ID, 대화 요약, prompt/LLM 출력 전문, 청크 본문, token·비밀값은 trace/log에 넣지 않는다. 고카디널리티 ID는 metric label에서 금지한다. 속성 allowlist·stage metric·대시보드·경보의 상세 계약은 [관측 계약](observability-contract.md)을 따른다.

## 4. 검증과 이후 도입 조건

첫 합격 증거는 **동일한 trace 화면**에서 Spring `journey.run` → FastAPI plan의 `query.preprocessing`/`query.interpretation`/`search.route` → Spring `plan_authorization` → private REST 기반 plan/execute hop → 정형 route일 때 선택된 Spring `PlaceQueryPort` adapter와 canonical SQL → FastAPI retrieval/generation(해당 route만) → Spring 최종 검증의 span parent 관계가 보이는 것이다. `SQL_ONLY`는 plan·approved execute·정형 lookup은 있지만 BM25/vector/RRF/reranker/generation은 없어야 한다. MCP를 채택하지 않은 환경에서 MCP span을 요구하지 않는다. 오류·provider timeout·reranker 복귀, export 차단·429·부분 전송, SSE 재접속과 삭제·철회 경로를 별도로 확인한다. 대시보드에서 수집 지연/유실·비용 추정과 실제 청구·RAG fallback·검색/생성 실패를 구분한다. 2GB 혼합 부하에서 계측 자체의 RSS·CPU·기존 API 지연 분포 퇴행을 측정한다.

Collector/Alloy는 직접 전송에서 유실·민감속성 필터·sampling 제어가 실제 문제로 나타나고 같은 호스트의 자원 측정이 허용할 때만 도입한다. Langfuse는 기존 Grafana와 별도로 LLM annotation/dataset 기능의 효용·비용·개인정보 보존을 입증한 뒤 검토한다. 품질 하락은 규칙 기반으로 검토 큐에 모으고 주간 Discord·이메일 요약으로 전달한다. `quality_harness`의 조사·격리 실험·설정 승격은 운영자가 명시적으로 시작하거나 승인한다.

## 5. 공개 Agent 관측 사례에서 가져올 설계 원칙

2026-10-22 공개 자료를 기준으로 [Claude Code 모니터링 문서](https://code.claude.com/docs/en/monitoring-usage)는 OpenTelemetry의 metric·event·선택적 trace를 분리해 사용량·비용·도구 활동을 집계한다. [Hermes Agent의 관측 계약](https://github.com/NousResearch/hermes-agent/blob/main/docs/observability/README.md)은 요청 단위 API hook에 시도 ID·provider·모델·시각·결과를 넣고, [gateway health exporter](https://github.com/NousResearch/hermes-agent/blob/main/agent/monitoring/gateway_health_export.py)는 상태 metric과 제한된 진단 이벤트를 in-process·fail-open 방식으로 보낸다. 이는 두 제품의 공개 **구현 참고 사례**이며, 온마루에서 같은 도구·스키마를 그대로 사용한다는 뜻은 아니다.

| 참고 원칙 | 온마루 적용 |
|---|---|
| 요청 실행과 운영 상태를 다른 신호로 관측 | `runId`/`traceId`로 단계별 span을 연결한다. 요청·오류·지연·quota·provider token 사용량은 낮은 카디널리티 metric으로 집계한다. 앱/DB/배치의 `up`·RSS·queue age·export 실패는 별도 운영 panel에 둔다. |
| provider 시도마다 결과·재시도 구분 | `generation` 아래 실제 API 시도별 span에 provider, 허용된 model ID, attempt 번호, latency, status/error code, token 수를 기록한다. prompt/응답 본문이나 개인 식별자는 싣지 않는다. 비용은 추정값과 실제 청구 확인값을 구분한다. |
| 관측 경로가 사용자 응답을 막지 않음 | bounded 비동기 exporter 실패를 경고 metric으로 세고 요청은 계속한다. 사용량 제한·권리 철회·최종 답변 확정은 기존 DB transaction과 검증 경로로 지킨다. |
| Trace의 공백을 영속 artifact로 보완 | 표본화·보존 만료 후에도 실패 유형, corpus/config/prompt/model version, 평가 fixture/hash, 근거 ID, 사람 판정이 품질 검토 큐에 남는다. 원문 대화의 보존·접근 정책은 제품 계약을 따른다. |

진단 흐름은 **Grafana 실패/지연 panel → exemplar 또는 허용된 로그의 `traceId` → Spring/FastAPI span 계층 → 제한된 `runId`로 품질 검토 항목 조회 → 재현 평가** 순서다. Prometheus label에 `traceId`·`runId`·회원 ID를 넣지 않는다. exemplar가 수집 경로에서 실제 지원되는지 확인하기 전에는 필수 탐색 경로로 간주하지 않는다. `quality_harness`가 분석할 때도 sampling된 trace만으로 원인을 확정하지 않고 영속 artifact와 corpus revision을 대조한다.
