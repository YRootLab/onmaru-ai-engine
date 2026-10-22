# 여정 질문 처리와 검색 계획 계약

> 상태: 구현 전 목표 설계. **`onmaru-ai-engine`의 FastAPI가 Query Processing Layer를 소유한다.** Spring은 회원·대화·공개 자격·정형 SQL·최종 게시 권한을 소유한다. Spring↔FastAPI plan/execute는 private REST 기준선으로 시작하고, trace에서 병목이 확인될 때 gRPC unary를 비교한다. 정형 데이터 접근은 Spring `PlaceQueryPort`를 통하며 private REST가 기본이고 MCP는 tool discovery/재사용이 필요한 경우의 선택지다. [Spring 경계 설계](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/ai-rag-spring/journey-query-mcp.md), [질문 해석 사전](question-understanding.md), [요청 생명주기](request-lifecycle.md)를 함께 적용한다.

## 입력에서 확정 계획까지

1. **Spring admission·privacy gate**: 인증·소유권·한도·입력 길이·idempotency를 검사한다. 회원 원문과 전체 대화는 Spring에 남긴다. 연락처·식별자·비밀키·자유 URL을 차단/제거한 최대 240자 `safeQuery`와 확정 구조화 대화 상태, 공개 후보 ID·허용 필터, 버전·상한만 내부 인증/TLS로 AI 엔진에 보낸다. 삭제하면 핵심 뜻이 바뀌는 질문은 AI에 보내지 않고 한 가지 확인 질문을 반환한다. Spring은 주제 코드나 검색 route를 정하지 않는다.
2. **AI Query Processing Layer**: AI 엔진이 세 단계를 수행한다. `Query Preprocessing`은 검색 표기·별칭을 정리하되 원문 의미를 보존한다. `Query Interpretation`은 의도·대상·조건·부정·확정 대화 맥락을 `QueryFrame`으로 구조화하고 불확실성/범위를 판정한다. 해석이 불확실하거나 대상이 충돌하거나 범위 밖이면 닫힌 `CLARIFY_OR_SCOPE` 결과를 낸다. `Search Router`는 `QueryFrame`을 받아 필요한 사실을 `CANONICAL_FIELD` 또는 `PUBLIC_PASSAGE`로 분해하고 승인된 다섯 경로 중 하나와 이유·정형 필드·검색 mode·fallback·config/corpus version을 결정적 규칙으로 제안한다. 원문을 코드 표시명으로 덮어쓰지 않으며, LLM이 매 요청 route/tool을 고르지 않는다.
4. **Spring authority gate**: 제안의 schema·version·route/field allowlist·source revocation·회원 소유권·공개/지역/고정/제외 범위를 검사한다. AI가 제안한 필터가 Spring의 상한보다 넓거나 canonical ID/필드가 허용되지 않으면 거부한다. 유효 계획은 Spring application service가 실행할 수 있도록 `ApprovedQueryPlan`으로 고정하고, 정형 조회에 30초짜리 opaque `queryGrantId`를 발급한다. 임의 SQL/DB 권한은 AI에 주지 않는다.
5. **Spring typed query 실행과 확정**: FastAPI의 결정적 `ApprovedPlanExecutor`가 정형 조회가 필요한 `SQL_ONLY`/`SQL_PLUS_RETRIEVAL` route에서만 `PlaceQueryPort`에 연결된 private adapter를 호출한다. 전송 방식은 MCP tool discovery의 재사용 이점이 확인되면 MCP, 고정 내부 호출만 필요하면 REST로 선택한다. 입력은 승인 grant뿐이며 Spring 내부의 고정 parameterized SQL template이 실행된다. `SQL_ONLY`는 Gemini·embedding·검색 없이 typed result를 deterministic renderer로 바꾼다. 복합 경로는 정형 결과와 FastAPI 내부 retrieval을 결합한다. Spring은 공개·철회·claim 근거를 재검증해 snapshot/SSE로 저장한다. 계획 승인 뒤 route를 바꾸지 않는다.

두 내부 호출은 하나의 `runId`·W3C trace·idempotency 범위에 속한다. 첫 **plan 호출은 로컬 규칙 처리이며 Gemini dispatch/회원 LLM 횟수 0회**다. 두 번째 execute 호출 직전 Spring이 사용량을 예약하고, 실제 provider dispatch 시작 시 원장에 1회를 확정한다. 계획 오류·서비스 장애 시 AI가 임의로 다른 경로를 실행하지 않고 Spring의 검증된 기본 탐색 또는 명시적 실패로 끝낸다. AI 엔진의 route 제안과 Spring 승인 결과는 별도 stage outcome으로 남긴다.

## Query Processing Layer 내부 경계

레이어는 별도 서버나 마이크로서비스가 아니다. FastAPI plan 요청에서 순서대로 실행되는 세 단계다.

| 단계 | 책임 | 산출물 |
|---|---|---|
| `Query Preprocessing` | 공백·표기·검수된 별칭 정리. 원문 표현·부정·수식 범위를 보존하고 정형화 문장으로 대체하지 않는다. | 원문 의미 보존된 검색 표현 |
| `Query Interpretation` | 의도, 대상, 주제, 긍정/부정 조건, 확정 대화 맥락, 모호성·범위 여부를 해석한다. | `QueryFrame` 또는 `CLARIFY_OR_SCOPE` |
| `Search Router` | `QueryFrame`에서 필요한 정형 사실/공개 본문을 분해하고 허용 route·mode를 결정적으로 제안한다. | 불변 `PlanProposal` |

첫 두 단계는 어떤 검색기를 사용할지 선택하지 않는다. route 선택은 Search Router가 담당하며, 실제 검색과 순위는 Spring이 계획을 승인한 다음 FastAPI execute 요청에서만 수행한다.

## 첫 릴리스의 결정적 경로

| 계획 | AI 엔진 선택 조건 | 승인 후 실행 | 실패 처리 |
|---|---|---|---|
| `SQL_ONLY` | 주소·지역·분류·공개 여부 등 등록된 정형 필드만 요구 | 승인 grant → Spring `PlaceQueryPort`를 통한 private REST typed call(기본; MCP 선택 가능) → 고정 renderer; LLM/임베딩 0회 | 필드·대상 미확정 시 확인 질문; 호출 오류는 명시 실패/승인된 기본 탐색 |
| `LEXICAL_ONLY` | 확정 장소 이름·검수 별칭·정확한 용어의 공개 본문 질문이며 개념 조합·비교·부정이 없음 | AI exact/prefix 식별 + 한국어 BM25; 필요 시 근거 제한 LLM 최대 1회 | 후보 0이면 근거 부족; 자동 vector 확장 금지 |
| `DENSE_ONLY` | 고유명사·부정·정확 용어가 없고 단일 의미 주제 | Semantic Search: 질문 임베딩 + pgvector exact cosine | 임베딩 오류면 승인된 기본 탐색; 자동 Keyword Search 재질의 금지 |
| `HYBRID` | 추천·수정·비교·역사/문화 설명처럼 표현이 다양하거나 이름과 의미를 함께 요구 | BM25 20 + vector 20 → RRF 최대 30 → reranker → 근거 최대 12 | 한쪽 장애는 동일 후보의 축소 실행과 사유 기록 |
| `SQL_PLUS_RETRIEVAL` | 주연산과 주소 등 부수 정형 사실 하나 | Spring typed lookup (private REST 기본; MCP 선택 가능) + AI 내부 `LEXICAL_ONLY`/`DENSE_ONLY`/`HYBRID` | Spring 호출 오류 시 정형 claim 제외; 독립 근거가 충분한 검색 결과만 표시. 검색 실패 시 검증 정형 값만 표시하거나 기본 탐색 |
| `CLARIFY_OR_SCOPE` | 핵심 조건 충돌·대상 불명확·미지원 실시간/외부 사실 | Spring 고정 질문/안내 renderer; 검색/LLM 0회 | 동일 |

라우팅 순서는 안전·모호성/범위 밖 → 정형만 `SQL_ONLY` → 정형+본문 `SQL_PLUS_RETRIEVAL` → 이름·별칭/정확 용어 단독 `LEXICAL_ONLY` → 부정·고유명사 없는 단일 의미 주제 `DENSE_ONLY` → 그 밖의 본문 복합 질문 `HYBRID`다. `SQL_PLUS_RETRIEVAL`의 본문 mode에도 같은 우선순위를 적용한다. `RRF`는 두 검색 경로가 실행된 계획에서만 적용한다. **다섯 경로 모두 첫 RAG 출시 범위**이며 route별 gold·권리·부정·지연·메모리 게이트를 통과해야 한다.

## 외부 API와 버전형 계획

외부 Wiki/검색 API는 첫 출시의 온라인 경로가 아니다. 추후 허용 도메인·라이선스·장소 매핑·개정·철회·timeout/429·캐시·비용을 승인한 뒤 별도 source adapter로 편입한다. 모델 주도 웹 탐색은 허용하지 않는다.

첫 출시에서 Spring↔FastAPI plan/execute는 private REST로 구현하고 trace로 왕복 지연을 계측한다. 병목이 확인되면 같은 versioned typed contract의 gRPC unary를 비교하며, 이는 bidirectional streaming을 뜻하지 않는다. Spring `PlaceQueryPort`는 이 orchestration과 구분되는 정형 조회 경계다. 그 adapter는 private REST가 기준선이고, MCP는 여러 client가 Spring AI tool catalog를 발견·재사용해야 할 때 적용한다. deterministic code가 승인된 lookup을 run당 최대 1회 호출하며 online model에게 자유 tool-calling loop를 주지 않는다. BM25·vector·RRF·reranker는 AI Engine 내부 typed component다. 품질 harness용 Spring read tool은 별도 principal로 격리한다. scope와 비교 기준은 [Spring 정형 조회 경계](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/ai-rag-spring/journey-query-mcp.md)와 [ADR-0019 제안](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/decisions/0019-journey-query-mcp-tools.md)에서 정의한다.

AI의 `PlanProposal`은 `{planVersion, route, retrievalMode, reasonCodes[], questionDictionaryVersion, configHash, corpusRevision?, sourceRevocationSequence, requestedCanonicalFields[], proposedFilters, positiveConceptCodes[], negativeConceptCodes[], targetPlaceIds[], semanticQuery?, limits}`의 닫힌 schema다. Spring은 `safeQuery`와 승인 가능한 공개 범위의 hash를 포함한 요청을 보내고, 제안의 필터가 허용 범위의 부분집합인지 검사한 뒤 `ApprovedQueryPlan`을 만든다. AI execute는 이 승인 계획의 hash가 plan 응답과 일치할 때만 실행한다. `semanticQuery`는 AI plan 응답→Spring 요청 메모리→AI execute 요청 사이에서만 일시 왕복한다. Spring/AI 영속 저장소·일반 로그·trace·외부 Gemini에는 남기지 않는다. `planHash`는 route·mode·필터·정형 필드·code/ID·semanticQuery 해시·version·runId를 정규 직렬화해 계산하고 양쪽이 동일하게 검증한다. AI 프로세스의 임시 상태에만 의존하지 않으며 plan/execute 불일치 시 재계획 없이 실패한다. `PlanProposal`, 승인 결과, 거부 이유, 실제 실행 경로의 version형 fixture를 양쪽 CI에서 검증한다.

평가셋은 정형·고유명사·의미 중심·복합·부정·동명이인·다턴·외부 사실 요청을 나눠 **AI 계획 선택 정확도**, Spring 승인 거부의 적절성, 불필요한 임베딩 호출, 잘못된 SQL 단독 응답, route별 근거 `Recall@K`/`nDCG@5`와 claim 지지를 본다. 실패한 gold 근거는 해석→계획→승인→검색→fusion/rerank 중 처음 사라진 단계로 분류한다. 운영 trace는 gold가 없으므로 정답 점수로 표시하지 않는다.
