# RAG 품질 평가와 환경 검증 계획

> 상태: 출시 전 실행 계약. 현재 수치는 설계 게이트이며 실측 결과가 아니다. [운영·평가](operations-and-evaluation.md)의 관측·비용 기준과 함께 적용한다.

## 평가셋 확대와 누설 방지

이전 60건(개발 40/봉인 20)·120건(개발 80/봉인 40) **계획**은 초기 smoke/중간 점검 단계로 두고, 다섯 실행 경로를 모두 여는 출시 판단 전 **최소 300건(개발 200/봉인 100)**을 실제 작성한다. 아래 route별 분포는 초기 하한이며 부정·다턴·동명이인·권리 철회·주입은 여러 route에 겹치는 별도 태그로 구성한다. 장소·원천 문서·질문 문형이 양쪽에 반복되어 답을 외우는 효과를 줄이기 위해 같은 장소/동일 source revision의 변형 질문은 한쪽 split에만 둔다. 실제 회원 대화는 동의 없이 복제하지 않고, 검수된 공개 장소와 합성 한국어 질문으로 만든다. 봉인셋을 반복 튜닝에 사용했다면 새 버전으로 교체한다.

| 기대 실행 경로 | 개발/봉인 최소 | 정답 라벨·중요 사례 |
|---|---:|---|
| `SQL_ONLY` | 35/15 | 주소·지역·분류·현재 공개 필드, 임베딩 0회 |
| `LEXICAL_ONLY` | 35/15 | 장소명·검수 별칭·고유명사·조사, 정확한 대상/근거 |
| `DENSE_ONLY` | 35/15 | 자연스러운 의미 표현·유의 표현, 명시 부정/고유명사 없는 단일 주제 |
| `HYBRID` | 60/30 | 추천·비교·역사/문화·복합 조건, 두 경로의 gold 근거와 RRF 전후 |
| `SQL_PLUS_RETRIEVAL` | 35/25 | 서로 다른 정형/본문 사실의 분리·합침, 동일 대상 검증 |

총계는 개발 200/봉인 100이다. 확인 질문·범위 밖·주입·개인정보·근거 부족·철회는 위 route별 질문의 기대 실행 **이전 차단/보류 태그**로 별도 fixture를 더한다. route별 봉인 15~30건도 드문 오류의 부재를 증명하지 못하므로 안전/권리 위반은 독립 계약 테스트와 전수 검수로 보완한다. 각 질문은 `queryId`, `threadContextFixture`, `sourceRevision`, `goldRoute`, `goldQuestionFrame`, 원문에서 보존해야 할 조건·표현 span, 안전한 `semanticQuery` 기대값/금지값, 허용/금지 장소, grade 0/1/2 장소·청크·source ID, 답변 가능 여부, 최소 사실 claim을 가진다. 두 사람이 독립 라벨링하고 불일치를 조정한다. 다턴 질문은 원문 전체 대화가 아니라 앞선 **확정 상태 fixture**를 재생한다. 데이터셋과 gold, source snapshot을 각각 hash로 고정한다.

### 합성 질의 제작·검수 절차

1. 공개 자격이 확인된 source revision과 canonical 장소에서 **질문 대상·정답 근거를 먼저** 정한다. 질문 생성은 사람이 직접 하거나 승인된 공개 자료만 사용한 보조 생성으로 한다. 모델이 제안한 질문·정답·장소 연결은 그대로 gold가 되지 않는다.
2. 추천·설명·비교·정형 사실·후속 수정과 다섯 route를 교차시켜 한국어 말투·동의어·부정·동명이인·정보 부족 사례를 작성한다. `조용한 곳` 같은 표현은 자료가 입증하는 범위와 현재 혼잡 보장을 구분한다. 답 불가·범위 밖 질문도 포함해 무조건 검색 결과를 내는 편향을 막는다.
3. 두 검수자가 원문 source offset과 장소 ID를 독립 확인하고 0/1/2 관련도를 부여한다. 불일치 조정 전 질문은 평가 job에 넣지 않는다. 같은 source의 문장만 바꾼 유사 질문은 같은 split에 묶고, 생성 모델이 본 문서·질문·해설이 봉인셋으로 새지 않았는지 provenance를 기록한다.
4. 각 case의 `datasetVersion`·source/corpus hash·gold 라벨·route·질문 사전 version을 고정한다. 개발셋은 실험에 사용하고 봉인셋은 승격 판정에만 사용한다. 운영 신호에서 합성 재현 질문을 만들 때도 공개 자료로 다시 검수하고 **다음 dataset version**에 넣는다.

이렇게 만든 합성 질의는 [품질 하네스](quality-engineering-agent.md)의 주간 replay와 config/corpus 변경 평가 입력이다. BM25·vector·RRF·reranker의 top-k를 같은 gold와 대조해 `Recall@K`, `MRR`, `nDCG` 등의 차이와 정답 근거가 처음 사라진 단계를 기록한다. Grafana의 운영 metric에는 gold가 없으므로 그 수치를 실시간 사용자 정답률로 표시하지 않는다.

## 단계별 지표·실패 원인

| 단계 | 계산 | 목표와 해석 |
|---|---|---|
| 질문 해석 | 정확한 route/frame 비율, `retrievalExpression`의 핵심 개념 보존율·부정 정확도, 잘못된 대상 결합 | 표현율 ≥0.90, 명시된 핵심 개념 누락·잘못된 부정/대상 결합 0. 확인 질문 정답 사례는 분리 |
| 질문 계획·라우팅 | 정형/본문/복합 gold의 `QueryPlan` 사실 분해·route/mode 정확도, 미사용 embedding 호출률, 승인 계획과 실제 실행 일치율 | 첫 출시 `SQL_ONLY`/`LEXICAL_ONLY`/`DENSE_ONLY`/`HYBRID`/`SQL_PLUS_RETRIEVAL`/확인 질문별 결과를 따로 보고. 허용되지 않은 route 실행·불필요한 embedding 0건. 단일 검색 경로의 정답 근거 누락과 오라우팅을 출시 전에 확인 |
| 원천 수집 | 예상 공개 문서 대비 적재율, hash 일치, 철회 지연 | 누락/철회 위반 0. 원천 자체가 없는 질문은 retrieval 분모에서 분리 |
| 청크 검색·재정렬 | gold 청크·source `recall@5/10/20/30`, `precision@5`, `MRR`, 후보 장소 수 | Keyword Search(BM25)/Semantic Search(vector) 각 20, 합집합·Hybrid Fusion(RRF) 30, reranker 12를 구분. gold 근거가 후보에는 있었으나 최종에서 사라진 비율과 추천의 서로 다른 장소 수를 기록 |
| 장소 선택 | 장소 `recall@5`, `nDCG@5`, 조건 위반 | 답 가능한 질문 기준 초기 gate recall≥0.85, nDCG≥0.75; hard filter 위반 0 |
| 생성 | claim 지지율, 인용 정확도, 답 불가 보류율, 누락된 필수 내용 | 사람 검수로 지지율 1.00, 보류율≥0.95. 분자/분모와 유형별 결과 동시 보고 |
| 전달/운영 | 확정 p95, 검색 p95, fallback·재접속·비용 | [운영 게이트](operations-and-evaluation.md)의 실험 부하와 동일한 조건 |

`precision@k`는 반환 청크 중 grade≥1 비율, `recall@k`는 gold 청크 중 반환된 비율, `MRR`은 첫 관련 청크의 역순위 평균이다. `nDCG@5`는 0/1/2 grade의 장소 순위를 평가한다. 답 불가 질문은 검색 점수 분모에서 제외하고 `적절한 보류` 분모로 옮긴다. 청크가 여러 개로 분할돼 동일 원천 단락을 가리키면 gold 문서 offset 기준으로 동치 처리해 청킹 변경을 공정하게 비교한다. 지표마다 질의 수와 정답 수를 같이 보고하며, 유형별 표본이 작으면 수치를 품질 보증으로 해석하지 않는다.

출시 전 추가 gate: 답 가능한 설명·추천 질문에서 gold 근거가 BM25/vector 합집합 40개 안에 있는 질의 비율 ≥0.90, RRF·다양성 후 reranker 입력 30개 안에 있는 비율 ≥0.90을 **각각** 충족한다. reranker 이후 최종 근거 12개의 장소 `recall@5`와 `nDCG@5`는 [운영 게이트](operations-and-evaluation.md)를 충족하고 RRF 기준선보다 어느 유형에서도 두 건 이상 악화되면 전수 검토한다. 추천 gold가 5곳 이상이며 hard filter가 허용할 때 reranker 입력에 서로 다른 장소 5곳 이상을 포함한다. 부정·동명이인·복합 질문은 별도 분모로 보고한다. 이 수치는 초기 가설이므로 개발셋에서 조정 가능하나 봉인셋 결과를 보고 사후 변경하지 않는다.

## 실험과 승격

첫 기준선은 현재 정형 기본 탐색이다. 같은 corpus snapshot/질의셋에서 `Keyword Search(BM25) 단독 → Semantic Search(vector) 단독 → Hybrid Fusion(RRF) → reranker → 청크 256/400/600 → overlap 0/60`을 단계별로 측정하고 후속 최적화는 **한 번에 한 축씩** 비교한다. 실험마다 corpus, dictionary, chunker, embedding, ranker, prompt, provider model, seed, 토큰 상한을 report에 저장한다. 품질이 좋아도 hard filter·철회·출처 위반 1건이면 승격하지 않는다. 자동 job은 후보를 보고하고, 사람이 실패 사례와 지연·비용을 검토한 뒤 version을 승격한다. 운영 데이터 변경으로 점수가 흔들릴 때는 수집→검색→생성을 분리해 진단한다.

100건 봉인셋도 드문 오류의 부재를 증명하지 못한다. 첫 운영 기간에는 사용자 신고와 익명 집계로 오류 유형을 수집하고, 승인된 합성 재현 사례를 평가셋의 **다음 버전**에 추가한다. 운영 질문을 자동으로 학습·평가셋에 옮기지 않는다.

## 환경 검증 매트릭스

| 환경 | 반드시 증명할 것 | 실패 시 조치 |
|---|---|---|
| 로컬 Docker PostgreSQL 17 + PostGIS + pgvector + BM25 확장 | extension 공존, 한국어 BM25 토큰화, `vector(384)` DDL·cosine 연산, 문서→청크 FK, 중복 manifest, active pointer 전환, 철회 우선, 복원 | schema/이미지 수정; 운영 이전 금지 |
| 로컬 Spring/FastAPI contract | 같은 사전 version, 원문 미전송과 `safeQuery`/`semanticQuery` 일시 처리, AI plan 제안→Spring 권한 승인→execute hash 일치, 검색 개념 보존·부정 처리, 후보 장소 다양성, reranker timeout/NaN/RRF 복귀, legacy 회원 탐색 재개·누락된 옛 답변 표시·철회 카드 배제, 후보/근거 allowlist, 409·멱등 재전송, SSE snapshot 재조회, ledger crash 시나리오 | API/fixture 수정 |
| 같은 호스트 FastAPI ↔ staging DB 내부 연결 | 외부 공개 없는 전용 Docker 네트워크 + TLS 인증·`pg_hba`, 공개 5432/FastAPI 포트 미노출, AI runtime role의 업무 schema 접근 거부 | 네트워크/role 수정; 공개 AI 차단 |
| 2GB 모델 포함 혼합 부하 | Spring·Nginx·PostgreSQL·FastAPI·질문 임베딩·reranker·SSE·정상 API·색인 배치의 동시 peak에서 OOM 0·DB 연결 고갈 0, 기존 API p95 퇴행 없음. 문서 임베딩은 피크와 직렬화하고 배치 시작/종료 순간도 측정 | JVM/DB/모델 메모리·batch/pool/동시성 조정 후 재측정; 그래도 실패하면 출시 보류 |
| 복구/장애 주입 | DB 재시작, source 철회 지연, FastAPI timeout, provider 429/5xx, SSE 단절, worker 중단, backup restore 후 revocation/삭제 재적용 | 같은 run fallback 또는 명시적 실패와 로그 분류 확인 |

부하 **가정값**은 출시 전 실제 트래픽 측정으로 보정한다. 2GB 모델 포함 staging은 먼저 동시 RAG run 1/2/5, SSE 연결 10/50/100으로 단계적으로 늘리고, 안정적일 때만 10/20 run·200 SSE를 탐색한다. 문서 1만/3만·평균 청크 3개, 일일 변경 100/1,000건을 조합한다. 각 조합은 10분 warm-up + 30분 측정, 세 번 반복하고 p50/p95/p99·모델 cold load·컨테이너/호스트 최대 RSS·`MemAvailable`·OOM·swap·DB I/O·WAL·인덱스 크기·기존 API latency·질의당 비용을 남긴다. 이 값은 **실제 수요 예측이 아닌 탐색 부하 단계**다. 현실 트래픽이 더 높으면 더 높은 단계를 추가한다. 동시 admission 상한은 2GB에서 통과한 단계 이하로 고정한다. latency SLO는 이 기준선과 제품 사용성 검토 후 별도 승인하며, 선결된 8초/1.5초 목표는 두지 않는다. 시스템 fallback 비율과 기존 API 퇴행은 별도로 판정한다. 기존 API 기준선이 없으면 먼저 staging에서 측정하고 허용 퇴행폭을 기록한 뒤 최종 출시 판정을 한다.

환경 검증은 로컬→staging 순서다. 운영 Lightsail 변경·공개 DB 포트 개방 없이 재현 가능한 로컬 테스트를 먼저 수행한다. 실행 결과에는 이미지 digest, PG/PostGIS/pgvector version, 코퍼스 건수, 인덱스 크기, 부하 도구 설정, 측정 날짜와 pass/fail을 기록한다. 실패를 문서 수정만으로 통과 처리하지 않는다.

### 2026-10-19 현재 환경 확인

`scripts/dbml2sql docs/database/schema.dbml --postgres` 변환, `node scripts/azimutt-export.mjs` 산출물 생성, `docker compose -f infra/local/postgres/compose.yaml config --quiet`, `bash scripts/verify-contracts`는 통과했다. 현재 로컬 Docker CLI는 있으나 daemon에 연결되지 않아 pgvector/PostGIS 동시 설치·실제 SQL·복구/부하 시험은 **미실행**이다. 현재 로컬 Compose 이미지도 PostGIS만 포함하므로 pgvector 포함 이미지와 migration을 마련한 다음 위 매트릭스를 실행해야 한다. staging의 같은 호스트 내부 TLS·FastAPI/모델 포함 2GB 혼합 부하도 아직 측정하지 않았다. 이 결과는 실행 가능한 환경 설정 확인이지 RAG 출시 게이트 통과가 아니다.
