# RAG 관측 스키마와 품질 하네스 입력 계약

> 상태: 구현 전 v1 목표 계약. [관측 계약](observability-contract.md)의 OTel span/metric과 [품질 감독](quality-engineering-agent.md)의 검토 큐 사이에 둘 **비식별 실행 결과**를 정의한다. 현재 FastAPI가 이 schema를 발행한다는 뜻은 아니다. JSON Schema 정본은 [`schemas/run-observation.v1.schema.json`](schemas/run-observation.v1.schema.json)이다.

## 1. 세 종류의 기록과 정본

| 기록 | 목적 | 누락 가능성·보존 |
|---|---|---|
| OTel trace/span | 개별 요청의 시간·부모 관계·오류 위치 조사 | sampling·export 실패·백엔드 보존 만료 가능. 하네스의 유일한 입력이나 감사 정본이 아니다. |
| Prometheus 호환 metric | route/stage별 분모·실패율·지연 histogram·비용 추세와 경보 | 집계이며 `runId`·`traceId`·회원 ID를 label로 넣지 않는다. |
| `RunObservation.v1` | 같은 run의 실행 계획·단계 결과·fallback·근거 판정을 재현 가능하게 요약 | Spring 소유 `runId`와 승인 버전으로 연결되는 접근 제한 artifact. 일반 품질 검토 후보는 최대 3개월 보존하며 철회·권리 감사 원장은 별도 정책을 따른다. |

FastAPI는 plan/execute 두 내부 요청의 허용된 `runId`를 echo하고, 실제 수행한 질문 해석·route 제안·검색/생성 단계의 `StageOutcome`을 응답 또는 제한된 비동기 artifact로 낸다. Spring은 실제 trace context에서 얻은 `traceId`, 공개/근거 최종 검증·영속화 결과를 결합해 한 `RunObservation`을 확정한다. **단일 writer는 Spring**이다. FastAPI가 회원 정보나 Spring DB run 행을 직접 조회·갱신하지 않는다. 응답 유실 시 Spring은 `observationStatus=PARTIAL`과 마지막 확인 단계만 기록하고, 없는 AI 단계 결과를 성공으로 채우지 않는다. 동일 `runId`·`schemaVersion` 재전송은 멱등 upsert로 처리하며 `stateVersion` 불일치는 거부한다.

## 2. 고정 단계·결과 코드

| 순서/조건 | `stage` | 진단할 경계와 핵심 계수 |
|---|---|---|
| plan 요청 진입 | `AUTH_CONTRACT`, `INPUT_PRIVACY` | Spring 비식별화, 내부 인증·schema·config/corpus version 검사 |
| AI 계획과 Spring 승인 | `QUERY_PREPROCESSING`, `QUERY_INTERPRETATION`, `SEARCH_ROUTING`, `PLAN_PROPOSAL`, `PLAN_AUTHORIZATION` | 표기 정리·의미 보존, QueryFrame 해석, route/정형 필드 제안, 권한·filter·version 승인/거절 |
| 필요 시 정형 조회·승인 실행 | `CANONICAL_SQL`, `APPROVED_PLAN_VALIDATION`, `QUERY_MATERIALIZATION` | Spring 허용 SQL, AI의 승인 plan hash 검증·검색 표현 준비 |
| `LEXICAL_ONLY`/`HYBRID` | `BM25_SEARCH` | DB 대기/실행, 검색·필터 후 후보 수 |
| `DENSE_ONLY`/`HYBRID` | `QUERY_EMBEDDING`, `VECTOR_SEARCH` | 모델 추론, 차원/profile, DB 대기/실행과 후보 수 |
| `HYBRID` | `RRF_FUSION` | 경로별 입력, 합집합·중복 제거 수 |
| 검색 뒤 | `CANDIDATE_POLICY`, `RERANK`, `EVIDENCE_SELECT` | 장소 다양성, 모델 추론·복귀, 철회/출처 제외·최종 근거 수 |
| 근거가 있을 때 | `CONTEXT_ASSEMBLY`, `GENERATION`, `PROPOSAL_PARSE`, `LOCAL_EVIDENCE_VALIDATION` | 문맥 token 예산, provider 시도별 결과, schema/claim·근거 판정 |
| Spring 마감 | `FINAL_VALIDATION`, `PERSISTENCE`, `SSE_DELIVERY` | 공개 자격 재검증, 확정 snapshot 저장, 최종 전송 |

`status`는 `SUCCESS`, `EMPTY`, `DEGRADED`, `FAILED`, `SKIPPED`다. `SKIPPED`는 실제로 실행하지 않았음을 뜻하지만 **필요할 때만 artifact에 이유와 함께** 남긴다. 미실행 경로의 OTel span은 생성하지 않는다. 한 경로 실패 후 다른 경로로 계속하면 실패한 단계는 `FAILED`, 요청 전체는 `DEGRADED`로 기록한다. reranker timeout 후 RRF 복귀도 `RERANK=DEGRADED`와 `fallback=RRF_ORDER`로 명시한다. 결과 없음(`EMPTY`)과 시스템 장애(`FAILED`)를 구분한다.

`errorCode`는 닫힌 enum으로 시작한다: `AUTH_REJECTED`, `SCHEMA_MISMATCH`, `VERSION_MISMATCH`, `PLAN_REJECTED`, `CONCEPT_LOSS`, `DB_TIMEOUT`, `DB_ERROR`, `EMBEDDING_ERROR`, `DIMENSION_MISMATCH`, `MODEL_TIMEOUT`, `MODEL_ERROR`, `INVALID_SCORE`, `SOURCE_REVOKED`, `EVIDENCE_EMPTY`, `PROVIDER_RATE_LIMIT`, `PROVIDER_TIMEOUT`, `PROVIDER_ERROR`, `RESPONSE_SCHEMA_INVALID`, `CLAIM_UNSUPPORTED`, `FINAL_POLICY_REJECTED`, `PERSISTENCE_ERROR`, `DELIVERY_INTERRUPTED`, `UNKNOWN`. 자유 오류 문구나 예외 전문은 schema 밖이다. `UNKNOWN` 비율을 관측해 코드 추가를 검토한다. `recovery`는 `NONE`, `OTHER_RETRIEVER`, `RRF_ORDER`, `VERIFIED_BASELINE`, `CLARIFICATION`, `FAILED_CLOSED` 중 하나다. 실제 사용자 결과와 무관한 임의 복구 코드를 agent가 변경할 수 없다.

단계별 `durationMs`는 단조 시계로 측정한다. 병렬 BM25/vector의 duration을 합산해 `retrieval` wall time으로 쓰지 않는다. DB client·provider HTTP의 자동 span은 단계 span의 자식으로 두고, SQL 전문·검색 표현·prompt/응답 본문은 기록하지 않는다. stage artifact에는 정수 후보 수·근거 수·허용/보류 claim 수와 고정 version/hash만 둔다. trace span의 속성 allowlist와 metric label 제한은 [관측 계약](observability-contract.md)을 따른다.

## 3. Trace·metric·artifact의 연결

```text
Grafana panel: stage=VECTOR_SEARCH, outcome=FAILED 증가
  → 허용된 로그/exemplar의 traceId로 단일 trace 조사
  → trace가 없어도 RunObservation(runId, versions, stage outcomes) 조회
  → gold fixture·corpus snapshot과 대조해 QualityReviewItem 생성
  → 운영자 선택 시에만 조사·ExperimentSpec·격리 실험
  → 결과 검토·승인 후 별도 배포 경로로 변경
```

`traceId`는 OTel SDK가 만든 값일 때만 연결한다. `runId`는 metric label에 넣지 않고 접근 제한 로그·artifact에만 둔다. `traceCoverage`는 `AVAILABLE`, `SAMPLED_OUT`, `EXPORT_FAILED`, `EXPIRED`, `UNKNOWN` 중 하나다. `EXPIRED`는 과거 평가 조회 시 판정하며 요청 당시 값으로 발행하지 않는다. `SAMPLED_OUT`과 `EXPORT_FAILED`를 추정으로 섞지 않는다. Grafana 전송 ACK만으로 `AVAILABLE`을 확정하지 않고 백엔드 조회 또는 별도 sampling 결정 근거로 검증한다.

## 4. 하네스가 자동으로 할 수 있는 일

| 입력·판정 | 자동 동작 | 사람/배포 경계 |
|---|---|---|
| 닫힌 `errorCode`, 누락 없는 단계 결과, 재현 가능한 단일 원인 | 결정적 분류·중복 묶기·`QualityReviewItem` 생성·템플릿 보고서 | 사용자 run의 검색 전략이나 운영 설정을 바꾸지 않는다. |
| 검색 후보 0/부정 조건 손실/claim 보류 등 품질 신호 | 운영 신호와 gold 재현 결과를 **다른 `evidenceLevel`**로 보관하고 대시보드·주간 요약에 집계 | 운영 신호만으로 정답 오류라고 확정하지 않는다. |
| 상충·누락된 artifact 또는 다중 원인 | `INSUFFICIENT_EVIDENCE`로 보류하고 필요한 trace/fixture를 제시 | 운영자가 명시적으로 요청한 경우에만 제한된 AI 조사. |
| 승인된 실험 계획·고정 snapshot | 격리 runner의 전후 평가·regression 계산 | 시작·예산·설정 승격은 기존 [품질 감독 권한 정책](quality-engineering-agent.md)에 따라 사람이 결정한다. |

하네스는 관측 사실과 제안된 원인을 구분한다. `StageOutcome`에 실패가 기록됐다는 사실은 확정적이지만, “chunk 크기 때문에 정답이 누락됐다”는 가설은 평가 fixture·반사실적 실험으로 검증해야 한다. 실험 결과가 좋아도 현재 요청을 되돌려 다시 생성하거나 운영 corpus/config를 즉시 수정하지 않는다.

## 5. schema 변경·검증

`schemaVersion=run-observation.v1`을 고정한다. 필수 필드 삭제·enum 의미 변경은 새 major schema와 양쪽 consumer 계약 테스트가 필요하다. 새로운 선택적 계수·단계는 schema와 stage allowlist·metric/dashboard·평가 fixture를 같은 변경에서 갱신한다. 최소 fixture는 정상 HYBRID, SQL_ONLY, vector 한쪽 실패, reranker timeout/RRF 복귀, 근거 0, provider timeout, 출력 검증 실패, trace 미수집, 응답 유실이다. 각 fixture에서 단계 존재/부재, 전체 상태, 사용량 ledger와 `RunObservation`의 일치를 확인한다.
