# W5 한국어 lexical 검색 구현 근거

## 구현 경계

- `KoreanTokenizer`는 NFKC/casefold와 제한된 조사 정규화를 수행하는
  `ko-simple-particle-v1` fallback profile이다. 형태소 분석기라고 간주하지 않는다.
- `KoreanBm25`는 `k1=1.2`, `b=0.75`인 결정적 BM25 기준 구현이다. `ts_rank`와
  `pg_trgm` 점수를 BM25로 부르지 않는다.
- `LexicalSearchAdapter`는 exact/prefix 이름·검수 별칭을 BM25보다 먼저 정렬하고,
  동일 점수는 `chunk_id` 오름차순으로 결정한다. 공개·revision·지역·분류·장소·제외·철회
  필터를 적용한 뒤 최대 20개만 닫힌 `CandidateSet`으로 반환한다.
- 검색 요청의 corpus/config/dictionary/revocation 버전은 `CorpusSnapshot`과 완전히 같아야
  한다. snapshot은 W3의 repeatable-read 트랜잭션을 그대로 사용한다.

## PostgreSQL 선택과 출시 게이트

`PostgresLexicalChunkRepository`는 BM25 확장으로 `pg_search`를 선택하고, 확장이 없으면
`BM25_EXTENSION_UNAVAILABLE`로 fail closed 한다. 운영 PostgreSQL image의 정확한 확장
버전·라이선스·한국어 tokenizer 호환성과 실제 BM25 index DDL은 BE 소유 image에서
확정해야 한다. 확정 전에는 이 adapter를 운영 활성화하지 않는다.

현재 W3 schema에는 검수 별칭 테이블이 없으므로 PostgreSQL projection은 공개 문서 제목을
exact 이름으로 사용한다. scorer 계약은 여러 `exact_names`를 받으며 한국어 별칭 fixture로
검증했다. 검수 별칭 저장·적재가 추가되면 repository projection만 확장한다.

## 검증 범위

- 조사 포함 장소명, exact 별칭, prefix 별칭, 동점 결정성
- 공개·revision·지역·분류·철회 hard filter 후 top 20
- 확장 부재, index version 불일치, snapshot version 불일치의 명시적 실패
- 빈 검색 결과의 `NO_EVIDENCE` 계약

PostgreSQL 확장 공존과 실제 index 성능·`EXPLAIN (ANALYZE, BUFFERS)`는 위 운영 image가
준비된 뒤 환경 검증 gate에서 수행한다.
