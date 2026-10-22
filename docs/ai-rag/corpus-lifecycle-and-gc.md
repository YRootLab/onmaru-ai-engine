# AI RAG corpus 보존·GC 정책

> 상태: 구현 전 운영 계약. 기간은 목표 2GB 운영 환경에서 검증할 초기값이며, 출시 전 권리 조건·복원 실험·실측 저장량으로 확정한다. 2GB 인스턴스 이전은 2026-10-23 오후 예정이며 아직 실행되지 않았다. 이 문서는 공개 검색 corpus에 적용한다. 회원 대화의 보존 기간은 [안전 정책](security-and-abuse.md)을 따른다.

## 보존 대상과 기산점

| 대상 | 초기 보존 규칙 | 삭제/예외 |
|---|---|---|
| 활성 corpus | `ai_active_corpus`가 가리키는 1개를 무기한 유지 | 검증된 새 revision 활성화 후 이전 것을 롤백 후보로 전환 |
| 롤백 corpus | 직전 활성 revision 1개를 전환 후 30일, 그 전 revision은 전환 후 14일 이내에만 유지. 최대 2개 | 최신 2개 중 기한이 남은 것만 보존. 철회·권리 취소가 반영되지 않은 revision은 즉시 롤백 부적격 처리 |
| `BUILDING` 중단본 | 마지막 진행 후 24시간 지나면 `REJECTED` 처리, 이후 72시간 이내 본문·벡터 삭제 | 진행 중 sync lease가 있으면 보류 |
| `REJECTED`/미승격 `VALIDATED` | 각각 종료 후 72시간/7일 이내 본문·벡터 삭제 | 조사 hold는 만료 시각·승인자·사유를 기록하고 최대 30일 후 재승인 |
| Spring의 RAG용 공개 정규화 export payload | 게시 후 30일, 그리고 sync 미완료 기간 중 더 긴 기간 | Spring canonical 원본과 구분. 철회된 payload는 권리 정책의 즉시 삭제 절차 우선 |
| manifest·문서 hash·출처/개정 식별자 | 게시 후 180일 | 본문·개인정보·원본 provider 응답 제외. sync 재현/삭제 증명용 |
| 철회 및 GC 감사 메타데이터 | 사건/삭제 완료 후 365일 | 대상 ID, source/corpus revision, hash, 사유 코드, 시각, 승인자/작업 ID, 삭제 결과만 저장. 본문·청크·벡터 금지 |
| 암호화 DB 백업 | 기존 [백업 정책](https://github.com/YRootLab/OnMaru-backend/blob/develop/infra/backup/policy.json)의 7일 | 별도 보관처. 복원 전 삭제 원장을 재적용하고 공개 자격을 재검증 |

일반 원천의 provider 원본 보존은 Spring 수집 정책과 공급자 권리 조건을 따른다. RAG가 provider 원본을 별도 복제하지 않는다. 30일 export payload를 DB 안에 중복 적재할지는 용량 측정 후 결정하며, 목표 2GB 호스트에 30일치 전체 snapshot을 무조건 쌓지 않는다. Spring이 적합한 비공개 저장소를 제공하지 못하면 이 계약을 충족할 때까지 자동 GC와 출시를 보류한다. 위 기간은 정책 제안이며 법적 보존 의무를 대체하지 않는다.

## 철회, 감사, 복원

공개 철회·권리 취소는 우선 Spring 공개 자격과 FastAPI 차단 집합에 적용한다. 일반 revision 만료를 기다리지 않는다. 철회 이벤트를 받은 뒤 **24시간 이내** 활성·롤백·staging 전체에서 해당 source revision 또는 장소의 `normalized_text`, `chunk_text`, `search_text`, `search_tsv`, embedding을 물리 삭제하고 인덱스에서 제거한다. 차단 집합은 감사 기간 동안 유지한다. 해당 행이 포함된 롤백본은 삭제·재검증 전까지 활성화 금지한다. 더 짧은 계약상 삭제 기한이 있으면 그 기한을 따른다.

감사를 위해 철회 **revision의 내용**을 따로 보관하지 않는다. `ai_revocation_events`와 별도 GC 감사 기록에 식별자·hash·처리 결과만 남긴다. 본문 재현이 필요한 정상 자료는 30일 export 기간 안에서만 가능하며, 그 이후 평가는 고정된 비본문 라벨/근거 ID로 수행한다. 과거 대화의 인용 표시는 저장된 제목·출처·revision 메타데이터로 유지하되, 재방문 시 현재 공개 자격을 다시 확인하고 철회 출처는 링크/본문을 숨긴다.

기존 백업에는 삭제 전 내용이 최대 7일 남을 수 있다. 백업 접근을 격리하고 자동 만료를 검증한다. 복원은 서비스 공개 전 철회·삭제 원장을 재적용하고 Spring 현재 공개 자격과 대조해야 한다. 감사 기록 보존 기간에 복원된 오래된 백업이 삭제를 되돌리지 못하도록 원장을 DB 백업과 독립된 접근 제어 저장소에도 보관한다. 원장 유실, sequence 누락, 재적용 실패 시 RAG를 닫는다.

## GC 실행 계약

1. 매일 저부하 시간에 후보를 계산한다. active pointer, 보존 기한, 롤백 후보 순위, 진행 중 sync, 질의 참조, 조사 hold, 철회 상태를 함께 조회한다. 후보 수·예상 바이트·사유를 먼저 기록한다.
2. 삭제 전 트랜잭션에서 active pointer와 revision 상태를 다시 검사하고 같은 revision에 대한 활성화/롤백/GC를 직렬화한다. 읽기 중인 요청은 시작 시 revision을 고정하며 종료 전 삭제하지 않는다. 중단된 요청 참조는 최대 2분 후 만료시키고, 만료 전 active 전환 중이어도 해당 revision을 보존한다.
3. 작은 배치로 embedding → chunk → document → 비활성 revision 순서로 지운다. 중간 실패 시 재시도 가능한 checkpoint를 남긴다. `ai_revocation_events`와 감사 기록은 별도 보존 규칙을 적용한다.
4. 삭제 건수·바이트·revision/hash·작업자·시각·재시도·hold를 감사 기록에 남긴다. 청크/embedding 고아 행 0건과 검색 결과 철회 ID 0건을 확인한다. `ANALYZE`/autovacuum 상태와 heap·index·WAL 증가를 관측한다. 운영 공유 DB에서 `VACUUM FULL`을 자동 실행하지 않는다.
5. 2회 연속 GC 실패, 만료 기한 초과, 롤백 후보 0개, 활성 revision 삭제 시도, 감사 기록 누락은 경보를 낸다. 마지막 두 경우에는 자동 삭제를 중지한다.

DB migration에는 revision별 GC 상태와 만료 시각, 조사 hold의 승인/만료, GC run/checkpoint/audit 테이블이 필요하다. 실제 DDL은 [저장 스키마](rag-storage-schema.md)와 `docs/database/modules/ai.dbml`을 함께 갱신한다. 출시 전 시계 이동·중복 실행·active 전환과 GC 경합·철회 후 롤백·7일 백업 복원·hold 만료를 staging에서 검증한다.

## 384차원 색인 개선 조건

`vector(384)`의 원시 float4 데이터는 청크당 1,536바이트다. 9만 청크면 한 revision의 벡터 값만 약 132MiB, 활성 1개와 롤백 2개면 약 396MiB다. 행·본문·인덱스·WAL·백업은 별도이므로 실제 저장량을 측정한다. 1차는 active revision과 공개/지역 후보를 먼저 제한한 exact cosine 검색을 유지한다.

revision별 청크 수, 필터 후 후보 수, `EXPLAIN (ANALYZE, BUFFERS)`, 검색 latency 분포, heap/index 크기, autovacuum 지연, 메모리와 WAL을 수집한다. 먼저 exact cosine 기준선과 실사용 평가를 만든 뒤, 검색 지연 또는 index/GC 부하가 실제 사용자 경험·2GB 호스트 여유를 해친다는 증거가 있으면 revision 단위 물리 분리, 부분 인덱스, 배치 크기, HNSW를 동일 평가셋에서 비교한다. HNSW 후보는 필터 후 recall@20, 최종 장소 품질, latency 분포, 색인 구축 CPU/메모리, 저장량, 철회/GC 지연을 exact 기준선과 함께 측정한다. 품질 퇴행 또는 메모리 초과 시 도입하지 않고 호스트 용량을 먼저 조정한다. 차원이나 embedding profile 변경은 새 revision 전체 재색인과 검색 격리를 요구한다.
