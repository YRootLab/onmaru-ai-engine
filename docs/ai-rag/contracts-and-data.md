# 홈 여정 대화 API·저장 모델 설계

> 상태: **목표 계약**. 아직 공개 OpenAPI·migration·코드에 적용되지 않았다. 구현 변경은 [Journey OpenAPI](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/contracts/openapi/journey.openapi.yaml), SSE schema, fixture와 [DB 설계](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/database/README.md)를 같은 PR에서 갱신한다.

기존 공개 계약을 확장하기 전 요청 처리 순서·Spring↔FastAPI envelope·실패 시 사용량 판정은 [요청 생명주기](request-lifecycle.md)와 맞춘다.
AI corpus의 revision·문서·청크·임베딩 테이블은 [RAG 저장 스키마](rag-storage-schema.md)와 [AI DBML](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/database/modules/ai.dbml)에 정의한다.

## 기존 자산과 식별자

`POST /api/v1/explorations`와 `POST /api/v1/explorations/{explorationId}/turns`는 현재 run을 만들고, SSE는 상태 알림을 전송하며, GET snapshot이 최종 결과다. `discovery_explorations`에 회원 소유자와 상태 버전, `discovery_turns`에 원문 질의, `discovery_runs`에 run이 이미 모델링돼 있다. 첫 대화형 버전의 `threadId`는 `explorationId`와 동일한 UUID다. 새 턴은 해당 탐색에 추가하고, 복제된 스레드를 만들지 않는다.

### 출시 전 기록의 이어보기

회원 소유의 기존 `discovery_explorations` 중 삭제되지 않고 접근 가능한 것은 새 thread 목록에 포함한다. `discovery_turns.query`로 과거 **사용자 질문**을 시간순 표시하고, 마지막 확정 `board`·pin/exclude·region·`state_version`을 현재 공개 자격으로 다시 검증해 후속 질문의 시작 상태로 삼는다. 이 기록에는 새 `discovery_turn_responses`의 확정 AI 답변·claim·citation이 없을 수 있다. 존재하지 않는 과거 assistant 메시지나 출처를 생성해 채우지 않고, 상세 화면에 `기존 탐색 결과`와 `이전 답변·출처는 저장되지 않음`을 표시한다. 공개가 철회된 카드는 이용 불가로 표시하고 새 추천/검색에 쓰지 않는다.

첫 후속 턴은 저장된 board와 명시 pin/exclude를 우선 사용한다. 과거 원문 질문에서 맥락을 재해석해야 하거나 대상이 불분명하면 확인 질문을 내며, 과거 AI 출력이나 미검증 proposal을 확정 메모리로 가져오지 않는다. 새 턴이 성공하면 그때부터 `discovery_turn_responses`와 `discovery_thread_context`를 기록한다. 회원이 아닌 guest 탐색의 자동 계정 귀속은 하지 않는다. 회원 소유권·삭제 조건을 적용한다. 새 설계의 회원 대화는 사용자가 삭제·탈퇴할 때까지 유지하며 이미 삭제된 과거 기록을 되살리지 않는다. migration은 기존 행을 대량으로 다시 생성하기보다 상세 조회 시 legacy 표시 상태를 계산하고, 첫 후속 턴에서 현재 `state_version`을 기준으로 맥락을 초기화한다. 이전/신규 기록 혼합 목록·빈 답변·철회 카드·삭제/탈퇴·타인 접근·첫 턴 동시 제출을 계약 테스트로 검증한다.

`saved-journeys`는 현재 특정 `sourceVersion`의 **읽기 전용 스냅샷**이다. 이번 기능의 찜은 변화하는 대화에 대한 북마크이므로 별도 리소스다. 마이페이지는 북마크된 thread를 현재 상태로 보여 준다.

## 공개 API 목표

모든 조회는 로그인 회원 본인 것만 반환한다. 타인 소유·삭제된 thread는 동일하게 404다. 쓰기는 기존 session/CSRF와 `Idempotency-Key`를 따른다. 모든 응답은 `Cache-Control: no-store`다.

| 메서드·경로 (`/api/v1` 아래) | 요청 | 성공·의미 |
|---|---|---|
| `GET /journey-threads` | `limit` 1..50 기본 20, `cursor?`, `bookmarked?` boolean | `items[{threadId,title,lastUserQueryPreview,updatedAt,latestRunStatus,bookmarked,placeCount}],totalCount,nextCursor,hasMore`; 최근 수정·ID 내림차순 |
| `GET /journey-threads/{threadId}` | 없음 | `threadId,explorationId,title,bookmarked,updatedAt,historyMode: FULL|LEGACY_PARTIAL,messages[],currentSnapshotUrl,activeRunId?`; 이전 기록은 저장된 사용자 턴과 현재 검증된 board만 표시 |
| `DELETE /journey-threads/{threadId}` | `Idempotency-Key`, CSRF | 204; 진행 중 run 취소 후 해당 회원의 턴·답변·요약·찜 삭제 |
| `PUT /journey-threads/{threadId}/bookmark` | `Idempotency-Key`, CSRF, 빈 본문 | 200 `{threadId,bookmarked:true,bookmarkedAt}`; 이미 찜했으면 같은 상태 |
| `DELETE /journey-threads/{threadId}/bookmark` | `Idempotency-Key`, CSRF | 204; 이미 해제됐어도 같은 결과 |
| `GET /me/ai-quota` | 없음 | `week{used,limit:5,resetsAt},month{used,limit:15,resetsAt}`; KST 창을 UTC instant로 반환 |

기존 `POST /explorations`, `POST /explorations/{id}/turns` 및 run/SSE/GET snapshot은 유지한다. 새 기능의 `CreateExplorationRequest`/`CreateTurnRequest`는 기존 `query`, `clientTurnId`, `baseVersion`, `regionCode` 등을 재사용하고 서버가 구조화 intent를 산출한다. 응답의 장소 목록은 유효한 장소가 충분하면 3~5개이고 부족하면 0~2개와 `THIN_RESULTS`를 포함한다. 별도의 `placeCount` 상한은 5다. 새 응답 계약은 `schemaVersion: "1.3"`으로 올리고 이전 `1.2` 클라이언트의 동작·필드 호환성을 fixture로 검증한다.

`messages[]`의 각 항목은 `{turnId, role: USER|ASSISTANT, text, createdAt, runId?, status: PENDING|COMPLETED|FAILED, places?, claims?, citations?}`이다. `places`는 현재 공개 자격을 다시 검사한 canonical ID·표시 정보만 담는다. `claims`는 `{text,evidenceIds[]}` 형태의 검증된 사실 문장만 담고, `citations`는 `{evidenceId, sourceType, sourceId, sourceRevision, title, publishedAt?}`이며 모델이 만든 URL을 포함하지 않는다. evidence ID는 저장 당시의 청크·문서 offset·source revision에 연결하고, 출처가 철회되면 해당 citation의 이용 불가 상태를 표시한다. 대화 화면은 옛 답변의 확정 당시 텍스트와 현재 장소의 이용 가능 상태를 구분해 보여 준다. 공개 철회 장소는 해당 카드의 이용 불가 상태로 표시하고 새 추천에 넣지 않는다.

SSE `run.stage`는 `INTERPRETING → RETRIEVING → VALIDATING → PERSISTING` 중 실제 도달한 단계만 보낸다. `run.text.delta`는 **검증·영속화한 확정 narration을 화면에 나누어 표시하는 선택적 이벤트**이며 기존 계약의 delta당 512자·run당 4,000자 상한을 지킨다. 모델 토큰의 직접 중계는 허용하지 않는다. 같은 `runId`의 단조 증가 `sequence`로 재연결한다. terminal/reset/재접속 뒤 GET run과 exploration snapshot을 읽어 표시 중인 텍스트를 확정 snapshot과 동기화한다. delta 없이 stage와 terminal만으로 완료해도 된다.

오류 코드는 기존 `AUTH_REQUIRED`, `NOT_FOUND`, `CSRF_INVALID`, `VERSION_CONFLICT`, `RATE_LIMITED`를 재사용한다. 주·월 한도에 걸린 여정 요청은 provider를 호출하지 않고 **같은 run의 기본 탐색**으로 완료하며 `degradedReason=AI_WEEKLY_QUOTA_EXCEEDED|AI_MONTHLY_QUOTA_EXCEEDED`와 두 창의 `resetsAt`을 snapshot에 포함한다. 둘 다 초과했으면 재설정이 더 늦는 월간 한도를 우선 표시한다. 그 외 provider/검색 실패도 별도 유료 재시도 없이 같은 run의 `engine=BASELINE`과 `degradedReason`으로 종료하며, 기본 탐색도 불가능하면 명시적 terminal 실패로 남긴다.

## 영속 모델 목표

| 모델 | 주 키·불변식 | 용도 |
|---|---|---|
| `discovery_explorations`/`discovery_turns`/`discovery_runs` | 기존 회원 소유·stateVersion·clientTurnId 유일성 유지 | thread, 사용자 원문, run 원천 |
| `discovery_turn_responses` 추가 | `turn_id` 유일, `run_id` 유일, 검증된 답변·장소 ID·claim별 evidence ID·source revision·생성/검증 version | 이어보기용 확정 응답. 미검증 모델 텍스트 저장 금지 |
| `discovery_thread_context` 추가 | `exploration_id` 유일, `state_version`, `intent_snapshot`, pins/exclusions, bounded summary, 갱신 시각 | 후속 턴의 구조화 메모리. 원본 턴에서 재생성 가능해야 함 |
| `journey_thread_bookmarks` 추가 | `(member_id, exploration_id)` 유일, `bookmarked_at`, 회원 소유 FK/검증 | 변화하는 대화 찜. `journey_saved_journeys`와 별개 |
| `journey_ai_dispatch_ledger` 추가 | `run_id` 유일, `member_id`, `dispatched_at`, `week_start_kst`, `month_start_kst`, provider outcome | 주/월 5·15회 한도. 실패·타임아웃도 dispatch 시작 시 1회 |

한도 검사와 ledger 예약은 **회원별 직렬화된 DB 트랜잭션**에서 수행해 두 동시 run이 같은 잔여 횟수를 쓰지 못하게 한다. ledger는 `RESERVED → DISPATCH_COMMITTED → SUCCEEDED|FAILED|UNKNOWN` 또는 `RESERVED → RELEASED`만 허용한다. `RESERVED`는 잔여 한도를 잠시 점유하지만 사용량에는 표시하지 않는다. transport 시작 직전에 `DISPATCH_COMMITTED`를 영속화하고 이 상태부터 사용량 1회로 센다. 확정된 동일 `runId`로는 provider를 다시 호출하지 않는다. 작업자가 죽은 `RESERVED`는 lease 만료 뒤 `RELEASED`로 되돌리고, `DISPATCH_COMMITTED`의 응답이 없으면 `UNKNOWN`으로 마감하며 사용량을 유지한다. 전송하지 않았음이 transport 기록으로 확실한 경우에만 운영 보정 절차로 환원한다. 네트워크 경계에서 원격 수신 여부를 완벽히 증명할 수 없으므로 UI에는 `LLM 전송 시도`를 사용량 기준으로 설명한다. 취소가 dispatch 전에 확정되면 `RELEASED`로 끝낸다. 읽기·SSE 재접속·중복 command replay는 ledger를 변경하지 않는다.

ledger의 `week_start_kst`·`month_start_kst`는 예약 시점이 아니라 `DISPATCH_COMMITTED` 시점의 KST 창으로 확정한다. 창이 바뀌면 같은 회원 잠금 아래 한도를 다시 검사한다. `DISPATCH_COMMITTED`와 transport 사이의 중단은 외부 수신 여부를 알 수 없으므로 자동 재호출도 자동 환불도 하지 않는다. 운영자는 request ID·전송 기록을 근거로 수동 보정할 수 있으며 보정 내역은 감사 로그에 남긴다. 이 정책은 정확한 외부 호출 횟수 보장이 아닌 **중복 호출 방지와 보수적 비용 회계**다.

`discovery_thread_context`는 회원 전체 프로필이나 개인 벡터 DB가 아니다. 최근 확정 의도와 사용자가 명시한 조건을 짧게 담고, 충돌 시 원본 턴·현재 canonical 상태를 재계산한다. 보존·삭제는 [안전·오남용 정책](security-and-abuse.md)을 따른다.

## 계약 검증

타인 thread/찜 404, 커서 페이지 순서·중복 없음, 동일 idempotency key 재전송, 두 동시 dispatch의 5/15 경계, 월요일·월초 KST 전환, 예약/전송 확정 사이 중단과 lease 회수, 확정 후 응답 유실 시 재호출 금지, dispatch 전 취소, provider timeout 후 재접속, terminal 전후 SSE replay, 삭제 중 active run, 기존 `saved-journeys`의 불변 snapshot을 각각 fixture와 DB 통합 테스트로 고정한다.
