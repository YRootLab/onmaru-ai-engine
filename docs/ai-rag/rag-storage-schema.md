# RAG 저장 스키마와 revision 전환 계약

> 상태: **구현 목표 논리·물리 설계**. [AI DBML](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/database/modules/ai.dbml)에 같은 개체를 반영한다. 실제 운영 변경은 별도 migration과 복구 검증을 통과해야 한다. Spring 업무 테이블과 FastAPI `ai` 스키마는 계정·소유권을 분리한다.

## 소유권과 키

`ai` 스키마의 모든 corpus 자료는 공개 자료만 담는다. Spring은 revision 고정 export를 제공하고 `ai` 테이블을 읽거나 쓰지 않는다. FastAPI runtime 계정은 승인된 DML/SELECT만, migration 계정은 DDL만 수행한다. `place_id`는 Spring canonical UUID의 복사 값이며 교차 스키마 FK가 아니다. 현재 자격은 최종적으로 Spring이 다시 판정한다.

DBML은 기존 저장소의 `ai_*` 논리 테이블명을 사용하지만 실행 migration의 물리 namespace는 `ai`로 고정한다. 구현 시 DBML 이름과 물리 `ai.*` 매핑을 migration 문서에 명시하고 같은 이름의 `public` 테이블을 새로 만들지 않는다. Spring 업무 migration과 FastAPI AI migration의 실행 순서·권한도 분리한다.

| 테이블 | 주요 열·제약 | 조회·운영 역할 |
|---|---|---|
| `ai_corpus_revisions` | `revision_id` PK, `manifest_hash` UNIQUE, `source_revision`, `state` (`BUILDING`,`VALIDATED`,`ACTIVE`,`RETIRED`,`REJECTED`), `embedding_profile_id`, `chunker_version`, `dictionary_version`, `document_count`, `chunk_count`, `created_at`, `activated_at` | staging/활성 revision 및 검증 결과 |
| `ai_active_corpus` | singleton PK `id=1`, `revision_id` FK, `revocation_sequence`, `activated_at` | 단일 원자적 active pointer |
| `ai_documents` | `(revision_id,document_id)` PK, `place_id`, `source_type`, `source_id`, `source_revision`, `title`, `published_at`, `collected_at`, `license_code`, `region_code`, `category_code`, `content_hash`, `normalized_text`, `eligibility_status` | 한 문서는 한 장소·한 출처 revision만 가리킴. `document_id`는 `source_type/source_id/place_id/source_revision`의 안정 해시 UUID |
| `ai_chunks` | `(revision_id,chunk_id)` PK, `document_id` FK, `ordinal`, `start_offset`, `end_offset`, `chunk_text`, `content_hash`, `search_text`, `search_tsv` | 원문 내 위치·청크 검색. `start_offset < end_offset`, 같은 문서의 `(ordinal)` UNIQUE |
| `ai_embeddings` | `(revision_id,chunk_id,embedding_profile_id)` PK/FK, `embedding vector(384)`, `normalized` | 첫 profile 전용. profile 교체 시 다른 차원 테이블/컬럼 migration과 전체 재색인, 혼합 검색 금지 |
| `ai_revocation_events` | `sequence` PK, `scope` (`SOURCE_REVISION|PLACE`), 대상 ID·revision, `revoked_at`, `reason_code` | Spring이 발행한 순서 있는 철회 원장과 ACK watermark |
| `ai_source_revocations` | `(source_type,source_id,source_revision)` PK, `last_sequence`, `revoked_at` | 특정 출처 개정만 차단. 새로 검수된 개정은 별도 자격 확인 후 적재 가능 |
| `ai_place_revocations` | `place_id` PK, `last_sequence`, `revoked_at` | 장소 전체가 비공개면 모든 출처 revision 차단 |
| `ai_corpus_sync_runs` | `run_id` PK, `revision_id`, `manifest_hash`, `state`, 단계별 건수/오류 코드, `started_at`,`finished_at` | 수집·파싱·임베딩·색인 실패 분리 |

실행 DDL의 필수 `CHECK`는 active pointer singleton=1, 문서/청크/임베딩 건수≥0, 청크 `ordinal≥0`·`0≤start_offset<end_offset`, 빈 본문 금지, revision state allowlist, 철회 scope별 필수 대상 필드다. `end_offset≤문서 길이`는 교차 행 검사이므로 수집 검증에서 강제하고 필요하면 trigger로 보강한다. 임베딩은 `vector(384)` 타입과 유한값/정규화 검증을 migration·적재 양쪽에서 확인한다. DBML이 표현하지 못하는 `CHECK`, `GIN gin_trgm_ops`, extension, 부분 인덱스, 권한은 migration에서 검증한다. `ai_chunks`의 문서 소속과 `ai_embeddings`의 청크 소속은 `(revision_id, id)` 복합 FK로 강제한다.

본문과 source ID는 공개 export의 검수된 값만 저장한다. `source_id`는 provider 내부의 불투명 식별자이며 URL을 모델이나 브라우저가 생성하지 않는다. 하나의 K-Content가 여러 장소에 연결되면 장소별 **별도 문서**를 만든다. 같은 청크에 장소·출처·revision을 혼합하지 않는다. 문서 수정은 기존 행 덮어쓰기가 아니라 새 corpus revision의 새 행으로 만든다.

## 인덱스와 질의

- `ai_documents(revision_id, region_code, category_code, place_id)` B-tree, `(source_type,source_id,source_revision)` B-tree. active revision의 필터를 먼저 적용한다.
- `ai_chunks`의 `search_text`는 검수 별칭·제목·본문을 구분자로 결합한 값이다. 첫 RAG 릴리스에는 한국어 토큰화 BM25 인덱스를 revision과 문서/청크 ID에 연결한다. 이름/별칭 exact 또는 prefix는 정규화된 별칭 테이블/표현식 B-tree로 보완한다. `pg_trgm`은 비교 기준선/보조 신호이며 `ts_rank`나 `pg_trgm`을 BM25라 부르지 않는다. BM25 구현 후보 `pg_search`의 실제 인덱스 DDL과 라이선스·호환성은 출시 게이트에서 확정한다.
- `ai_embeddings`의 첫 profile은 `vector(384)`와 cosine 거리 `<=>`를 사용한다. 1차는 지역/공개 후보를 먼저 제한한 뒤 exact distance 정렬을 한다. `EXPLAIN (ANALYZE, BUFFERS)`로 후보 수·sort·메모리·p95를 남긴다. HNSW는 실제 병목일 때만 별도 revision/부하 실험으로 도입한다.
- `ai_source_revocations`는 source revision 기준, `ai_place_revocations`는 장소 ID 기준으로 적용한다. Spring의 current eligibility는 place ID와 source revision을 모두 검사한다. corpus 안의 `eligibility_status`만으로 현재 공개 여부를 결정하지 않는다.

검색은 `(active revision, embedding profile, dictionary version, revocation watermark)`를 한 읽기 snapshot으로 잡는다. retrieval 결과에는 이 네 값과 `document_id`, `chunk_id`, `source_revision`을 함께 실어 최종 검증과 재현에 쓴다. `max 20`은 BM25/dense **각각의 필터 후 청크** 수다. RRF 최대 30개를 reranker에 넘긴 뒤 장소별 최대 2개·전체 근거 최대 12개를 적용한다.

## 적재·활성화·철회 순서

1. Spring manifest의 문서 수·해시·공개/권리 목록을 검증하고 `BUILDING` revision을 생성한다. 중복 manifest는 같은 sync run의 결과를 재사용한다.
2. 공개 문서 정규화 → 단락 chunk → metadata/offset → 같은 profile의 passage 임베딩 → BM25/vector 인덱스를 **비활성 revision**에 기록한다. 청크 수·embedding 수·dimension·NaN/빈 벡터·출처/장소 불일치·문서 hash를 검사한다.
3. 제한된 질의 smoke와 revocation 적용 결과를 확인해 `VALIDATED`로 만든다. 같은 transaction에서 이전 pointer와 manifest version을 비교하고 `ai_active_corpus.revision_id`를 갱신한다. 실패한 revision은 검색에 보이지 않는다.
4. 철회 이벤트는 `ai_revocation_events.sequence`로 멱등 수신하고 scope에 따라 source revision 또는 장소 차단 집합에 반영한다. 이미 처리한 sequence 재전송은 무시하고, 중간 sequence가 빠졌으면 watermark를 올리지 않는다. Spring의 heartbeat에 현재 sequence와 발행 시각을 담아 이벤트가 없는 정상 상태와 전파 중단을 구별한다. 검색 시 active revision과 두 차단 집합을 함께 조회한다. 이벤트가 역전·누락되거나 watermark가 60초 이상 뒤처지면 RAG를 차단한다. 같은 출처가 재승인되면 새 `source_revision`을 만들고 이전 철회 revision은 계속 차단한다. Spring의 최종 공개 자격 검사는 독립적으로 유지한다.
5. rollback은 이전 **검증된** revision으로만 하며 현재 차단 집합은 유지한다. 오래된 revision이 철회 자료를 다시 노출할 수 있으면 rollback하지 않는다. 활성 1개와 롤백 최대 2개, 중단본·철회 자료의 우선 삭제, 조사 hold와 감사 보존, GC 경합 제어는 [corpus 보존·GC 정책](corpus-lifecycle-and-gc.md)을 따른다. migration에는 revision별 GC 상태/만료, hold, GC run/checkpoint/audit 구조를 추가한다.

`ai_active_corpus`와 revision state 변경은 하나의 migration owner/운영 절차로 관리한다. FastAPI runtime은 활성 포인터를 임의로 바꾸지 못하도록 별도 sync role을 쓴다. DB 복원 시 pointer·revocation watermark·현재 Spring 공개 자격을 재검사하고 불일치하면 RAG를 닫는다.

## 용량 산식과 migration 검증

사전 용량 추정은 `문서 수 × 평균 청크 수 × (384×4 바이트 벡터 + 청크 본문/metadata + 행·인덱스 오버헤드) × 동시 보존 revision 수`로 계산한다. 실제 heap/index/TOAST/WAL 크기는 샘플 적재 후 DB에서 측정한다. 예정된 2GB 호스트에서 색인 배치와 API의 부하가 기준을 넘으면 배치 직렬화·청크/인덱스·pool을 조정해 재측정하고, 미통과 시 RAG 출시는 보류한다.

실행 migration은 PostGIS·pgvector·BM25 확장을 포함한 PostgreSQL 17 이미지에서 extension 생성, 차원 제약, FK/UNIQUE/CHECK, BM25/B-tree, 권한, 중복 적재, 철회·rollback, 백업 복원을 검증한다. DBML의 `vector(384)`는 목표 논리 계약이며 현재 운영 extension이 설치됐다는 뜻이 아니다. 테스트 순서는 [평가·환경 검증](evaluation-and-environment-tests.md)을 따른다.
