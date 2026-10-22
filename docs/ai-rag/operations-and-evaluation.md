# 홈 여정 AI RAG 운영·평가 설계

> 상태: 구현 전. [아키텍처](architecture.md)의 출시 게이트와 후속 품질 개선을 구분한다. 평가셋 구성·지표 정의·환경 시험의 실행 계약은 [평가·환경 검증](evaluation-and-environment-tests.md)을 따른다.

## 인프라·검색 엔진 선택

기존 1GB/$7 Lightsail의 PostgreSQL/PostGIS에 pgvector와 BM25 검색을 추가하기 전에, 사용자가 선택한 **2GB/$12 Lightsail 단일 인스턴스**로 스냅샷 이전한다. 이전 후 Spring·PostgreSQL/PostGIS/pgvector/BM25·Nginx·FastAPI·질문 임베딩·reranker를 새 서버 한 대에서 실행하고 문서 임베딩·색인 배치도 같은 호스트에서 시간대를 분리한다. 기존 Compose의 Spring 448MiB·DB 320MiB·Nginx 64MiB 제한 합계는 832MiB로, 1GB에는 FastAPI/모델을 단순 추가할 여유가 거의 없었다. 2GB에서도 CPU 평균 약 2%만으로 메모리·순간 부하를 보증하지 않는다. 이전 전후 `MemAvailable`, swap, OOM, 컨테이너 RSS/peak, DB 연결·디스크 여유·p95를 기록하고, OS/Docker/파일 캐시 여유를 남긴 **동시 peak 메모리 예산표**와 cold/warm 혼합 부하로 검증한다. Compose 제한·JVM heap·DB pool·FastAPI worker·모델 적재/동시성 값은 2GB 측정 뒤 고정한다. 출시 게이트를 계속 통과하지 못하면 운영 확장을 진행하지 않고 추가 서버·상위 플랜은 별도 결정으로 다룬다.

인스턴스 이전은 **2026-10-23 금요일 오후(KST) 예정**이며 아직 수행하지 않았다. 스냅샷 생성·새 인스턴스 준비·PostgreSQL 백업·고정 IP 전환·롤백의 정확한 절차는 [Lightsail 2GB 마이그레이션 runbook](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/operations/runbooks/lightsail-2gb-migration.md)을 따른다. 서버 이전과 RAG 기능 출시를 별도 변경으로 검증한다.

별도 $5 벡터 DB·FastAPI 서버는 만들지 않는다. FastAPI는 기존 Lightsail Compose의 독립 컨테이너로 두고 Spring·DB와 **외부에 공개되지 않는 전용 Docker 네트워크**에서만 통신한다. `5432`와 FastAPI 포트는 호스트에 publish하지 않으며 Nginx는 FastAPI에 직접 라우팅하지 않는다. 서비스 간 인증, DB 서버 인증 TLS(컨테이너 DNS 이름과 인증서 검증), `pg_hba` 제한, `ai` 스키마의 runtime/migration 분리 최소 권한 계정과 secret 분리를 검증한다. 호스트 방화벽과 외부 포트 스캔으로 노출이 없는지 확인한다. 동일 호스트라는 이유로 업무 schema 권한이나 TLS 검증을 생략하지 않는다.

### 2GB 프로세스·메모리 예산 계약

배포 전에 실제 Lightsail에서 host `MemAvailable`, swap, OS/Docker RSS와 기존 Spring·DB·Nginx의 idle/피크를 측정한다. `Spring heap/native + PostgreSQL shared buffers/backend/cache + Nginx + FastAPI runtime + 질문 임베딩 + reranker + OS/Docker 여유`의 **동시 peak**가 2GB 한도에 들어가는 배분표와 Compose `mem_limit`/worker/pool 값을 제출한다. 기존 832MiB 제한 합계는 새 인스턴스에서도 기준선으로 측정하고, FastAPI/모델 제한을 OS 여유와 함께 배분한다. 우선 FastAPI worker 1개, 배치와 온라인의 동시 실행 금지, 한정된 후보·토큰 길이, 모델 중복 적재 방지·양자화 후보를 비교한다. 같은 모델을 문서/질문 임베딩에서 공유할 수 있는지와 reranker 적재 방식은 실제 한국어 품질·cold/warm 지연으로 판정한다. 모델을 끌 때마다 요청 지연이 늘 수 있으므로 `메모리만 절감`한 결과를 합격으로 보지 않는다.

온라인 RAG가 처리 중이면 문서 임베딩·재색인 batch는 시작하지 않고, batch 중 새 요청은 admission 상한과 현재 가용 메모리에 따라 대기 상한 내 수락하거나 같은 run의 검증된 기본 탐색으로 종료한다. 배포·복원·백업·GC와 batch가 겹칠 때의 peak도 시험한다. swap thrash, OOM, DB connection 고갈 또는 기존 API 퇴행이 나타나면 batch를 중단하고 신규 RAG admission을 닫는다. 기존 사용자 응답의 철회·권한 검사는 유지한다. 2GB 합격을 위해 임의로 BM25·vector·reranker를 빼거나 근거 게이트를 낮추지 않으며, 품질/지연/자원 조건을 동시에 통과하지 못하면 출시를 보류한다.

| 선택지 | 판단 |
|---|---|
| PostgreSQL BM25 확장 `pg_search` + pgvector | 첫 RAG 릴리스의 1차 구현 후보. PostgreSQL 17·PostGIS·pgvector 동시 설치, 한국어 토크나이저, AGPL 의무와 2GB 공존 한도·색인 성능을 검증한다. [ParadeDB](https://github.com/paradedb/paradedb) |
| `pg_trgm` + pgvector | 이름·별칭 exact/prefix 보조 및 BM25 비교 기준선. BM25 점수로 표기하지 않으며, BM25 게이트 실패를 숨기는 운영 대체재로 자동 승격하지 않는다. |
| 자체 운영 Elasticsearch | Basic 소프트웨어는 무료지만 JVM heap·파일 캐시와 별도 운영 자원이 필요해 목표 2GB 공유 서버에는 넣지 않는다. [Elastic 요금](https://www.elastic.co/pricing/self-managed), [메모리 지침](https://www.elastic.co/docs/reference/elasticsearch/jvm-settings) |
| AWS OpenSearch Service | 무료 티어는 자격·기간·사양 제한이 있으며 관리형 클러스터/Serverless는 인스턴스·OCU·스토리지 과금이 있다. 현재 예산에서 제외한다. [AWS 요금](https://aws.amazon.com/opensearch-service/pricing/) |

## 운영 전 검증 게이트

1. 현재 DB의 `pg_dump`/볼륨 스냅샷을 복구 연습하고, PostGIS+pgvector+BM25 확장 버전 고정 이미지를 같은 PostgreSQL major로 빌드한다. 세 extension의 공존·한국어 토큰화·차원·거리 연산과 기존 PostGIS 질의 회귀를 확인한다. 라이선스·이미지 공급/패치 경로를 기록한다.
2. 원천 export의 공개·권리 필터, manifest 해시, 중복 동기화, 실패 revision 격리, tombstone 검색 제외, active pointer 전환·롤백을 fixture와 staging에서 검증한다.
3. 목표 2GB 한도를 재현한 환경에서 정상 API + SSE 동시 연결 + 상주 FastAPI·질문 임베딩·reranker + 검색 부하를 측정한다. 별도 시나리오로 문서 임베딩·BM25/vector 재색인 batch와 온라인 요청의 **전환 경계 및 강제 겹침**을 주입해 직렬화/admission이 작동하는지 확인한다. 온디맨드 staging이 같은 호스트에서 켜질 수 있다면 동시 배포 순간도 포함한다. OS 여유, OOM·swap, 각 컨테이너 RSS/peak, 모델 cold load, PostgreSQL RSS·connection·buffer/cache, 두 index 크기, 디스크 여유·I/O queue, 단계별 p95와 Spring API p95를 기록한다. 2GB에서 통과해야 출시한다. 수치가 불안정하면 모델·pool·batch·색인 방식을 재설계하고 재측정하며, 반복 실패 시 출시는 보류한다.
4. 같은 호스트의 FastAPI가 DB TLS 인증 실패, 허용되지 않은 컨테이너/계정, 업무 스키마 접근 시 거부되는지와 외부 스캔에서 `5432`·FastAPI 포트가 보이지 않는지 확인한다. 개인 원문·토큰·비밀키가 provider 요청과 로그에 없는지 테스트한다.
5. 이전 60/120건은 smoke·중간 점검으로 사용하고, 다섯 경로의 첫 출시 전 고정 한국어 질의 **최소 300건**을 개발 200건·봉인 평가 100건으로 실제 작성한다. route별 하한과 별칭·부정·복합·다턴·근거 부족·철회·주입의 겹침 태그를 포함하고, 원문→비식별 `semanticQuery`의 의미 보존/개인정보 차단과 장소·청크·출처 관련도·정답 가능 여부를 두 명이 검토해 불일치를 조정한다. SSE 재접속·동시 한도는 별도 계약 fixture로 검증한다. 허용되지 않은 장소/출처/회원 접근 0건, 누락 근거의 허위 확정 0건이 필수다. release 후보와 현재 기본 탐색을 같은 셋에서 비교한다.

### 1차 출시 측정 계약

아래 수치는 **초기 설계 게이트**이며 업계 보편 수치나 현재 성능 실측값이 아니다. staging에서 고정 corpus·모델·질의셋과 예상 동시 부하로 측정하고, 충족하지 못하면 출시 전에 설계/용량을 바꾸거나 근거를 남겨 게이트를 재결정한다. 운영 입력은 동의 없이 평가셋에 복사하지 않는다.

| 지표·분모 | 초기 게이트 | 판정 방식 |
|---|---:|---|
| 인증·소유권·공개/철회·제외·출처 ID 위반 | 0건 | 계약 fixture와 봉인셋 전수 검사; 1건이라도 출시 중단 |
| 답 가능한 질의의 장소 `recall@5` | ≥ 0.85 | gold 장소 ID의 top 5 포함; 빈 정답 집합은 분모에서 분리 |
| 관련도 `nDCG@5` | ≥ 0.75 | 장소 grade 0/1/2, 질의별 평균; BM25·dense·RRF·reranker를 동일 gold에서 각각 보고 |
| 사실 claim의 근거 지지율 | 1.00 | 봉인셋의 모든 사실 claim을 사람 2명이 확인; 불일치 조정 기록 |
| 답 가능한 질문의 `questionFrame`·`semanticQuery` 의미 보존율 | ≥ 0.90 | 원문의 핵심 주제·대상·연산과 허용된 수식·부정 범위를 code/ID 및 비식별 검색 문장에 함께 보존한 비율; 미표현·개인정보 불확실 사례는 확인 질문으로 전환 |
| 잘못된 대상·주제 결합 | 0건 | 지시어·동명이인·부정 조건을 포함한 계약 fixture |
| 답 불가 질의의 적절한 보류율 | ≥ 0.95 | 정답 가능 여부가 `false`인 질의 별도 분모 |
| 요청 접수 후 첫 진행 표시 p95 | 기준선 측정 후 결정 | 동일 리전 staging, REST 접수부터 첫 `run.stage` 또는 고정 로딩까지 측정 |
| RAG 검색·재정렬 p95 | 기준선 측정 후 결정 | 필터·BM25·dense·RRF·reranker 전체, 단계별 및 warm/cold cache 분포 기록 |
| 확정 snapshot 완료 p95 | 기준선 측정 후 결정 | REST 접수부터 DB 확정/terminal까지 측정; fallback도 포함 |
| 시스템 원인 fallback 비율 | ≤ 5% | 정상 RAG 대상 run 중 검색/DB/provider/검증 장애 fallback; 근거 부족·한도 초과는 별도 |

300건도 희귀 유형별 성능을 통계적으로 보증하지 않는다. 필수 유형마다 개발·봉인 최소 수를 [평가셋 표](evaluation-and-environment-tests.md)에 고정하고 유형별 분자·분모를 별도 공개한다. 100건 봉인셋의 실패 사례를 전수 검토하며 점수 하나로 미세한 품질 차이를 확정하지 않는다. 새 모델·청킹·ranker를 고를 때는 데이터 누설 없이 셋을 확장한다. 기존 1~3개 proposal용 [평가 하네스](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/ai/evaluation-harness.md)의 threshold를 새 3~5개 RAG에 그대로 복사하지 않는다.

### 요청 시간·비용 예산

현재 사용자 응답의 p95/SLO 숫자는 선결하지 않는다. 먼저 동일 환경에서 요청 접수→첫 진행 표시→각 retrieval 단계→provider→최종 검증·저장까지 기준 분포를 수집하고, 운영자의 실제 사용성·무료 provider 제한·2GB 자원 여유를 함께 검토해 단계별 deadline과 목표를 정한다. 각 단계의 absolute deadline은 상위 run deadline 안에 있어야 한다. timeout·취소·queue 포화 시 두 번째 모델 호출 없이 같은 run의 검증된 기본 탐색 또는 명시적 실패로 종료한다. 정확한 동시 run 상한·DB pool 크기·batch worker 수와 latency SLO는 혼합 부하 기준선 및 staging 결과를 바탕으로 정하고, 결정 근거와 측정일을 이 문서에 기록한다.

회원 답변은 Gemini API 무료 tier로 시작한다. 운영 API key가 무료 프로젝트에 속하는지, 과금 계정·유료 key·초과분 결제로 자동 전환되지 않는지 배포 전에 확인한다. 모델별 input/output token 상한, 무료 tier의 실제 RPM/TPM/RPD 할당량과 429 처리, 하루·월간 dispatch 예산을 모델 ID와 함께 배포 설정에 고정한다. 사용량·실패한 dispatch·fallback 비율을 따로 기록한다. 유료 tier로 전환할 때는 별도 사용자 결정과 현재 단가 확인, 일·월 hard cap 및 가격 확인일을 설정한다. 무료 tier의 실효 비용이 0이어도 같은 호스트의 FastAPI·모델·관측 자원 사용량과 Lightsail 실제 청구액은 따로 측정한다. 의미 캐시는 회원 대화 조건·현재 corpus revision·공개 철회 때문에 1차에는 도입하지 않는다. 캐시를 검토한다면 소유권·revision·철회 무효화와 비용 절감 실측이 선행돼야 한다.

공개 철회 또는 이용 권리 취소 이벤트는 Spring의 현재 공개 자격에서 즉시 반영하고, FastAPI 차단 집합 전달은 **60초 이내**를 초기 운영 목표로 측정한다. 차단 집합 확인이 60초를 넘거나 실패하면 RAG를 닫는다. 최종 응답은 항상 Spring의 현재 공개 상태를 다시 검사하므로 차단 전파가 지연돼도 철회 장소·출처를 노출하지 않아야 한다. tombstone 검색 제외와 구 revision 재활성화 금지는 staging에서 강제로 지연·역순 전달해 검증한다.

## 분리된 관측·실패 진단

| 오프라인 수집·색인 | 온라인 검색·생성 |
|---|---|
| 원천 revision·문서 수·권리 제외·해시 오류·청크 수·임베딩 실패·tombstone 지연·active pointer lag·BM25/vector 색인 CPU/메모리 | route(SQL/RAG)·검색 개념 보존/확인 질문 수·필터 통과 수·BM25/dense 후보와 고유 장소 수·RRF/rerank/최종 근거 수·rerank timeout/절단/RRF 복귀·단계별 p95·provider 지연/토큰·출처 검증 실패·fallback·SSE 중단/재접속 |

두 흐름에 `traceId`, `runId`, `corpusRevision`, `embeddingProfile`, `rankerVersion`, `promptVersion`을 연결하되 문서 본문·회원 원문·정밀 위치는 로그와 일반 메트릭에 넣지 않는다. 수집 실패, 검색 무응답, 생성 검증 실패를 다른 `failureStage`로 기록해 원인을 분리한다. Grafana 알림은 sync lag/실패, DB 메모리·디스크, 온라인 fallback 상승, provider 비용 상한을 각각 감시한다.

## 2차 평가·개선 루프

개발셋과 봉인된 평가셋을 분리하고, 사람 검토로 관련 장소·근거·정답 가능 여부를 라벨링한다. retrieval은 `precision@k`, `recall@k`, `MRR`, `nDCG@5`, hard-filter 위반과 출처 신선도를 본다. 생성은 claim groundedness, 인용 정확도, 누락·과장, 답변 유용성, 적절한 답변 보류를 평가한다. 첫 릴리스의 BM25·vector·RRF·reranker 각 단계 기여를 측정하고, 이후 한국어 analyzer, 청크 크기/overlap, RRF 상수, reranker 모델을 **한 축씩** 바꾸어 같은 revision에서 비교한다. 자동 평가가 후보를 제안할 수는 있지만 production ranker·모델·prompt의 자동 승격은 금지하고 사람의 결과 검토와 rollback 가능성을 요구한다. 피드백·찜·클릭은 제품 지표이며 정답 라벨로 자동 간주하지 않는다.

평가 job은 corpus 공개 revision, chunker/embedding/ranker/prompt 변경 PR, 그리고 주간 예약 실행에서 같은 고정 질의셋을 재생한다. 산출물에는 질의 ID, 정답 근거 ID, top-k 결과, 생성 claim별 인용 지지, 각 단계 지연·토큰/비용, 모든 version과 기준선 대비 차이를 남긴다. 자동 job은 퇴행을 표시하고 후보 설정만 제안한다. 운영 승격은 사람이 실패 질의와 비용·지연·출처 위험을 검토한 뒤 version을 고정하고 이전 version으로 되돌릴 수 있을 때만 한다. 실제 회원 질의는 동의 없이 평가셋으로 복사하지 않는다.

평가 보고서를 읽는 agent는 누락된 원천·질문 해석·BM25/vector 검색·RRF·reranker·생성 중 어느 단계에서 실패했는지 가설과 재현 실험을 제안할 수 있다. 승인되지 않은 문서·모델·prompt·색인 설정을 자동 반영하지 않는다. 구체적인 도구 allowlist, 입력 보존, 승인 상태와 효과 측정은 [품질 감독 설계](quality-engineering-agent.md)를 따른다.
온라인 run trace와 gold 평가 결과의 비동기 연결, `FailureCase` 판정, 반사실적 실험, 격리 runner, review gate, 모델/도구 비용 상한은 [RAG Quality Engineering 상세 설계](quality-engineering-agent.md)를 따른다. 관측 도구 장애는 사용자 답변의 결과를 바꾸지 않지만 trace 유실률을 경보로 관리한다.

## 단계

1. 계약·ADR·OpenAPI 변경과 공개 projection/권리 확인.
2. 2GB 기준선·로컬/격리 staging의 PostGIS+pgvector+BM25·비공개 연결·복구·혼합 부하 검증. 실패하면 2GB 안의 자원·색인·배치를 조정해 재측정하고, 미통과 상태에서는 출시하지 않는다.
3. 코퍼스 export→청킹/metadata→임베딩→active revision, SQL/하이브리드 라우팅과 근거 검증.
4. 회원 대화·한도·SSE·FE 목록/찜, 장애 fallback과 staging 전체 흐름 검증.
5. 출시 후 평가셋 확장, BM25 tokenizer·reranker 모델·청킹 개선과 계측 기반 용량 조정.
