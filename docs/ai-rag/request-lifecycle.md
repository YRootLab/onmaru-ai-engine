# 홈 여정 RAG 요청 생명주기와 실패 결정표

> 상태: 구현 전 목표 설계. 공개 필드와 오류 코드는 [API·저장 모델](contracts-and-data.md)에, 제품 화면은 [PRD](prd.md)에 정의한다. 아래 내부 envelope는 구현 시 확정할 경계 계약이며 현재 API에 존재하지 않는다.

허용 코드·동의어·부정/복합 판정은 [질문 해석 사전](question-understanding.md), claim별 출처의 허용·보류는 [근거 검증 정책](grounding-and-review.md)을 따른다.
AI 엔진의 정규화→계획→라우팅, Spring의 계획 승인, 첫 출시의 모든 검색 경로 선택 조건은 [질문 처리 계약](query-processing.md)을 따른다.

## 요청당 불변식

- `threadId = explorationId`; 한 thread에서 활성 run은 최대 하나다. `clientTurnId`와 `Idempotency-Key`를 같은 회원·thread 범위에서 재전송하면 기존 turn/run과 최종 결과를 반환한다.
- 서버가 확정한 canonical 장소 ID와 source revision만 최종 응답에 남는다. 모델이 생성하는 미검증 문장은 SSE에 싣지 않는다. `run.text.delta`를 사용한다면 최종 검증·저장된 답변의 표시용 조각만 재생한다.
- FastAPI는 회원 식별자·쿠키·원문 질문 전체·원문 대화 이력을 받지 않는다. Spring이 비식별화한 `safeQuery`, 확정 구조화 맥락, 허용 공개 범위·후보 ID만 계획 호출에서 받는다. AI가 생성한 `semanticQuery`는 승인 실행까지 두 내부 요청의 메모리에서만 왕복하고 외부 LLM·저장소·로그에는 보내지 않는다.
- 모델 dispatch 전에는 사용량을 차감하지 않는다. dispatch 시작 후 실패·timeout·응답 유실은 1회로 센다. 같은 run에서 두 번째 LLM 호출을 하지 않는다.
- 후속 턴의 `baseVersion`이 현재 `stateVersion`과 다르면 409를 반환하고 새 run을 만들지 않는다. FE는 최신 snapshot을 읽어 사용자가 다시 제출하도록 한다.

## Spring ↔ AI 엔진 처리 순서

1. **Spring 접수**: 세션·CSRF·회원 소유권, 입력 크기, `clientTurnId`, `baseVersion`, 속도·활성 run을 검사한다. 최근 확정 6개 턴의 구조화 상태와 제한된 요약을 읽고 철회된 카드·ID를 제거한다. 원문은 Spring에 보관하며 개인정보·비밀·자유 URL을 차단/제거해 `safeQuery`를 만든다. 삭제가 핵심 뜻을 바꾸면 확인 질문을 반환한다. `LEGACY_PARTIAL` thread는 저장된 board·pin/exclude·region만 현재 공개 상태로 재검증하고 저장되지 않은 옛 답변을 추정하지 않는다.
2. **AI 계획 호출**: Spring은 `runId`, `safeQuery`, 확정 구조화 상태, 공개 후보/필터의 상한, corpus/config/사전 version, trace context를 내부 인증/TLS로 FastAPI에 보낸다. Query Processing Layer의 preprocessing·interpretation 단계가 표기와 대상·부정·다턴 지시어를 처리해 `QueryFrame`·`retrievalExpression`·`semanticQuery`를 구성한다. 이어 Search Router가 닫힌 `PlanProposal`을 만든다. 모호성/미지원은 `CLARIFY_OR_SCOPE`로 반환한다. 이 호출은 로컬 규칙 실행이며 Gemini/회원 LLM 횟수 0회다.
3. **Spring 권한 승인·grant 발급**: `PlanProposal`의 ID·정형 필드·필터가 허용 범위의 부분집합인지, version·철회 sequence가 맞는지 검사한다. 승인되지 않으면 실행하지 않는다. 정형 조회가 있으면 Spring application service가 실행할 고정 query plan을 만들고, 그 plan에만 쓸 수 있는 30초 opaque grant를 발급한다. AI에는 임의 SQL 문자열이나 업무 DB 계정을 주지 않는다.
4. **승인 계획 실행**: Spring은 승인 plan hash·grant reference·version을 private REST 기준선의 FastAPI execute orchestration call에 전달한다. FastAPI의 고정 `ApprovedPlanExecutor`는 `SQL_ONLY`/`SQL_PLUS_RETRIEVAL`에서만 Spring `PlaceQueryPort`의 기본 private REST adapter를 최대 1회 호출한다. 공통 tool discovery 필요가 확인돼 MCP를 별도로 선택한 경우에만 MCP adapter를 쓴다. 검색은 FastAPI 내부 typed BM25/vector/RRF/reranker component에서 수행한다. `semanticQuery`는 승인 실행까지 일시 왕복하며 영속화·로그·trace·Gemini 전달을 금지한다. AI process 재시작 또는 plan/execute hash/version 불일치 시 재계획/재생성하지 않고 같은 run의 승인된 기본 탐색 또는 명시적 실패로 끝낸다. 실제 provider dispatch 시작부터 한도 1회를 확정하며, timeout/응답 유실에도 추가 호출하지 않는다. Spring↔FastAPI REST hop의 지연이 운영 trace에서 병목으로 확인되면 동일 계약의 gRPC unary를 별도 staging 실험으로 비교한다.
5. **Spring 최종 확정**: 반환된 후보·근거·claim을 현재 공개·철회·회원 조건·정형 값과 재대조하고, 확정 답변·카드·citation·요약·`stateVersion`을 원자적으로 저장한 뒤 terminal SSE를 보낸다. 미검증 모델 문장은 보내지 않는다.

## 내부 Spring ↔ FastAPI 두 단계 envelope 목표

### 1단계: plan 요청과 AI 제안

```json
{
  "runId": "<uuid>",
  "safeQuery": "<개인정보 제거·의미 보존된 최대 240자 질문>",
  "confirmedContext": {"regionCode": "<code>", "pinnedPlaceIds": [], "excludedPlaceIds": [], "lastConfirmedPlaceIds": []},
  "authorityBounds": {"allowedPlaceIds": [], "allowedRegionCodes": [], "allowedCanonicalFields": ["PUBLIC_ADDRESS"], "filterHash": "<hash>"},
  "versions": {"corpusRevision": "<active>", "configHash": "<hash>", "questionDictionaryVersion": "<version>", "sourceRevocationSequence": "<sequence>"},
  "limits": {"bm25K": 20, "vectorK": 20, "rerankK": 30, "evidenceK": 12, "maxPlaces": 5}
}
```

AI 응답의 `PlanProposal`은 `route`, `retrievalMode`, `reasonCodes`, `questionFrame`, `retrievalExpression`, `requestedCanonicalFields`, `proposedFilters`, `semanticQuery?`, `planHash`와 입력 버전 echo를 포함한다. Spring은 계획의 권한·공개 필터·정형 필드 요청을 검증해 `ApprovedQueryPlan`과 필요한 경우 MCP용 opaque grant를 만든다. `safeQuery`와 `semanticQuery`는 두 내부 호출 사이 요청 메모리에만 둔다.

### 2단계: 승인 plan 실행

```json
{
  "runId": "<same-uuid>",
  "approvedPlanHash": "<plan-hash>",
  "approvedRoute": "SQL_PLUS_RETRIEVAL",
  "approvedFilters": {"filterHash": "<same-authority-bound>"},
  "queryGrantId": "<opaque-short-lived-reference-or-absent>",
  "semanticQuery": "<AI가 생성한 비식별 로컬 검색 문장>",
  "versions": {"corpusRevision": "<same-active>", "configHash": "<same-hash>", "sourceRevocationSequence": "<current>"}
}
```

AI는 plan의 `runId`·입력 version·filterHash·route·mode·`semanticQuery` 해시와 승인 계획을 다시 대조한다. `queryGrantId`는 정형 조회가 승인됐을 때만 존재하며 selected Spring adapter에는 이 grant 외의 질의 조건을 전달하지 않는다. 네트워크 재전송은 grant-bound idempotency key와 plan hash가 같은 경우에만 허용하고 새로운 검색 전략을 만들지 않는다. 실제 application contract는 `PlanProposal`/`ApprovedQueryPlan`/`ExecuteRequest`와 [정형 조회 contract](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/ai-rag-spring/journey-query-mcp.md) 및 전송 adapter fixture로 고정한다.

`questionFrame`은 원문을 되풀이하는 텍스트 슬롯이 아니다. 버전이 고정된 주제 사전의 code, canonical ID, `RECOMMEND|EXPLAIN|COMPARE|REFINE` 연산만 허용한다. `retrievalExpression`은 승인된 **긍정 개념·부정 개념·공개 엔티티 ID**를 담는다. AI 엔진은 Spring의 `safeQuery`에서 `한적한`, `아이와`, `걷기 좋은` 등 허용된 표현의 실제 수식 관계와 부정 범위를 비식별 `semanticQuery`에 보존하고 각각 `QUIET`, `FAMILY_SUITABILITY`, `WALKABLE` 같은 코드에도 결합한다. FastAPI는 사전 version·plan과 의미 일치를 검사한 뒤 BM25·질문 embedding·reranker에 semanticQuery를 사용한다. 코드의 표시명만 이어 붙여 사용자 표현을 대체하지 않는다. 부정 개념은 긍정 BM25 문자열에 섞지 않고 hard exclusion이 가능한 경우 필터에 적용한다. 개인정보 제거로 문장 의미가 바뀌거나 표현할 수 없는 부정이면 확인 질문을 낸다. 사전 version 불일치나 핵심 개념 손실은 RAG를 호출하지 않고 확인 질문/기본 탐색으로 돌린다. `GENERAL`로 뭉개지 않는다. 원문 전체와 semanticQuery는 외부 LLM에 전달하지 않는다.

`retrievalExpression`은 긍정 개념 최대 4개, 부정 개념 최대 2개, 공개 엔티티 ID 최대 2개이며 중복 code를 제거하고 사전의 정렬 순서로 직렬화한다. `questionFrame`의 대상·주제·연산과 충돌하면 요청을 거부한다. 다턴에서는 새 턴의 명시 개념이 같은 속성의 오래된 맥락을 대체한다. `semanticQuery`는 비식별 `safeQuery`의 허용된 여행 표현과 필요한 확정 조건만 포함하며 길이 240자 이하다. Spring은 원문→`safeQuery`의 삭제 span을, AI 엔진은 `safeQuery`→`semanticQuery`의 보존 span 및 코드·ID·부정 범위를 확인한다. 검색 문장과 tokenizer 입력을 로그에 저장하지 않고 code·dictionary version·해시·길이만 기록한다. 생성 규칙과 fixture를 Spring/FastAPI가 같은 version으로 검증한다.

`confirmedTurnStates`는 원문이 아니라 지역·테마·place ID·필터 연산처럼 검증된 값만 담는다. `boundedSummary`도 자유 서술문이 아닌 allowlist 필드의 직렬화로 제한한다. 추적 ID는 내부 서비스 인증 토큰과 별개이며, `runId`로 회원을 조회할 수 있는 FastAPI 권한은 주지 않는다. 실제 네트워크 계약은 버전 필드와 JSON schema를 추가해 고정한다.

FastAPI execute 응답은 `configHash`, `corpusRevision`, `sourceRevocationSequence`, `candidatePlaceIds`, 장소별 `reasonClaims[{claimId,text,kind,evidenceIds}]`, `summaryClaims[]`, `sourceRevision`, `retrievalStatus`, `generationStatus`, `failureStage`로 닫힌 schema를 사용한다. 자유 `narration` 필드는 공개 출력에 사용하지 않는다. Spring은 요청과 다른 config/corpus 응답, 미등록 ID·출처·URL·HTML·필터 밖 ID·철회 revision을 폐기한다. 응답의 철회 sequence가 현재 sequence보다 뒤처지면 최신 자격을 재조회하고 검증 불가능 시 기본 탐색으로 끝낸다. citation은 모델 문장에 적힌 URL이 아닌 evidence registry의 ID로 조립한다. 이 필드들은 **목표 내부 계약**이며 구현 시 JSON schema·fixture와 함께 버전을 올린다.

## 검색과 확정의 세부 순서

1. Spring이 공개·지역·분류·고정/제외 필터의 현재 상한을 승인한다. FastAPI는 활성 corpus revision의 동일 구조화 필터, `retrievalExpression`, 비식별 `semanticQuery`로 한국어 BM25 상위 20, dense 상위 20을 **병렬** 검색한다. 이름·검수 별칭 exact/prefix는 canonical ID 식별에 활용한다. 추천·교체에서는 각 경로가 장소당 최대 3개, 같은 source revision당 최대 2개 청크만 남기되 20개를 채우려면 더 깊이 스캔한다. 설명은 대상 장소, 비교는 명시된 두 장소를 각각 검색하여 이 다양성 제한을 적용하지 않는다.
2. 중복 청크를 합치고 `1/(60+bm25Rank) + 1/(60+vectorRank)`로 결합한다. 추천·교체는 RRF 상위 30개를 뽑기 전에 장소당 최대 3개를 적용하고, 가능한 서로 다른 장소 최소 5곳을 먼저 확보한다. 조건에 맞는 장소가 5곳 미만이면 실제 수를 기록한다. 설명·비교는 대상별 근거를 보존한다. reranker가 최대 30개를 재정렬한 뒤 장소당 최대 2개, 전체 최대 12개 근거를 선택한다. 별칭 exact hit는 canonical ID 매핑 후 dedup한다. reranker 오류·timeout은 같은 후보의 RRF 순서로 복귀하고 degraded 상태를 기록한다. `pg_trgm`을 BM25로 표기하지 않는다.
3. 근거가 0개면 LLM을 호출하지 않고 `THIN_RESULTS` 또는 기본 탐색으로 끝낸다. 후보가 1~2곳이면 확인된 수만 답하고 부족 이유를 붙인다. 근거가 있어도 현재 공개 조건을 위반하면 그 항목을 버린다.
4. FastAPI는 후보·근거 ID의 allowlist 안에서만 제안한다. 문장별 `claims[{text,evidenceIds}]`를 반환하고 Spring은 각 claim의 근거가 같은 장소·활성 revision에 속하는지 검증한다. 의미상 지지 여부를 기계적으로 확증할 수 없으므로 검증되지 않은 사실 문장은 보류하고, 초기 출시의 자동 검사와 사람 검수 평가를 함께 적용한다. citation은 서버 evidence registry에서 만든다.
5. Spring은 카드의 현재 공개 상태와 필터를 다시 확인한다. 검증 후에만 확정 snapshot을 쓰고, 이후 대화 요약을 같은 stateVersion으로 갱신한다.

## SSE·FE 상태 전이

Query Processing Layer의 단계와 사용자 표시 단계는 별개다. `query.preprocessing`, `query.interpretation`, `search.route`는 각각 trace에서 분리하지만 FE에는 하나의 `INTERPRETING` 진행 상태로 보인다. `SQL_ONLY`는 검색이 없으므로 `RETRIEVING`을 건너뛰고 최종 검증·저장으로 간다. `HYBRID`는 Keyword/Semantic Search, RRF, reranker의 실제 실행 span을 남기되 FE에는 `RETRIEVING`으로 묶는다. `LEXICAL_ONLY`/`DENSE_ONLY`에서는 실행하지 않은 검색 경로·RRF의 span이나 진행 문구를 생성하지 않는다. 이 매핑은 [모듈 경계](module-boundaries-and-pipelines.md)와 같은 버전의 fixture로 검증한다.

| 상태 | 들어오는 이벤트·조건 | FE 동작 | 영속 결과 |
|---|---|---|---|
| `ACCEPTED` | REST command 응답에 `runId` | 사용자 문장 표시, 입력 잠금 | 사용자 턴·run |
| `INTERPRETING` | `run.stage` | 오목 로딩과 해석 안내 | 답변 없음 |
| `RETRIEVING` | `run.stage` | 근거 탐색 안내 | 답변 없음 |
| 생성 진행 | `run.stage` 또는 heartbeat | 오목 로딩과 고정 진행 문구만 표시 | 답변 없음 |
| `VALIDATING`/`PERSISTING` | `run.stage` | 근거 확인 안내; 미검증 문장 노출 없음 | 검증된 snapshot 저장 |
| 확정 내용 표시 | 저장 완료 뒤 선택적 `run.text.delta` | 이미 확정된 문장만 점진적으로 표시 | 확정 snapshot이 먼저 존재 |
| `COMPLETED` | terminal 또는 GET run | GET snapshot과 일치시켜 카드·citation 표시, 입력 해제 | 확정 답변·카드·citation |
| `FAILED`/`CANCELLED` | terminal 또는 GET run | 로딩 종료, 실패/기본 탐색 안내 | 실패 또는 검증된 fallback |

`run.text.delta`는 모델 토큰의 직통 중계가 아니다. 사용자에게 문장이 점차 나타나는 경험을 제공하려면 **최종 검증된 답변을 저장한 뒤** 최대 512자씩 분할해 보낸다. 따라서 생성 중에는 stage/고정 진행 문구만 보이는 구간이 있다. 이벤트 `sequence`는 run 안에서 단조 증가하고 `Last-Event-ID` 재연결은 같은 run의 저장된 이벤트만 replay한다. replay 범위 밖이거나 terminal 이벤트를 놓치면 GET run·snapshot이 판정 기준이다. FE는 재연결만으로 새 command를 발행하지 않는다.

## 실패 결정표

| 위치·조건 | LLM 사용량 | 같은 run의 결과 | 운영 `failureStage` |
|---|---:|---|---|
| 입력·권한·version 거부 | 0 | HTTP 오류; run 미생성 | `REQUEST` |
| 모호한 조건·범위 밖 | 0 | 확인 질문/고정 안내 | 없음 |
| 질문 정규화의 핵심 의미 손실·대상 충돌 | 0 | 한 가지 확인 질문; 검색하지 않음 | `INTERPRETATION` |
| 계획 version·허용 route·필터 불일치 | 0 | 확인 질문/검증된 기본 탐색 또는 명시 실패 | `PLANNING` |
| FastAPI의 계획 거부·내부 위임 실패 | 0 | 검증된 기본 탐색 또는 명시 실패 | `ROUTING` |
| 주/월 한도 초과 | 0 | 검증된 기본 탐색 + quota reason | `QUOTA` |
| 활성 색인 없음·revision 불일치·검색 timeout | 0 | 검증된 기본 탐색 또는 명시적 실패 | `RETRIEVAL` |
| 근거 0건 | 0 | 부족한 결과/기본 탐색; 추측 금지 | `RETRIEVAL_EMPTY` |
| dispatch 이후 provider timeout·오류 | 1 | 재호출 없이 기본 탐색 또는 명시적 실패 | `GENERATION` |
| 생성은 성공했지만 형식·출처·현재 공개 검증 실패 | 1 | 제안 폐기 후 기본 탐색 또는 명시적 실패 | `VALIDATION` |
| SSE 연결만 끊김 | 추가 0 | 기존 run replay 또는 snapshot 재조회 | `DELIVERY` |

기본 탐색도 현재 공개 자격과 소유권을 통과해야 한다. `failureStage`는 내부 관측 필드이며 FE에는 `degradedReason`과 이해 가능한 안내만 보인다. 검색 한 경로만 빈 경우에는 남은 경로로 계속하되 degraded 상태와 후보 수를 기록한다. 조회 가능한 과거 확정 답변은 새 run 실패로 지우지 않는다.
