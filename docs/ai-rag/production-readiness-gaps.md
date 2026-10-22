# AI RAG·품질 감독 운영 준비 검토

> 상태: 2026-10-21 설계 검토. 목표 계약과 현재 구현을 구분한다. 이 표의 `미검증`은 기능 결함 확정이 아니라 출시 증거가 없다는 뜻이다.

## 판정 원칙

현재 운영 서버는 1GB/$7이며 2026-10-23 금요일 오후(KST)에 [2GB/$12 인스턴스 마이그레이션](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/operations/runbooks/lightsail-2gb-migration.md)을 진행할 예정이다. **아직 이전하지 않았다.** 사용자 결정에 따라 새 2GB 단일 호스트에서 PostGIS·pgvector·BM25·Spring·Nginx·FastAPI·임베딩·reranker가 공존하는 것이 RAG 출시 조건이다. 현재 Spring/DB/Nginx 컨테이너 제한 합계는 832MiB지만 새 호스트의 실제 가용량과 FastAPI/모델 peak는 미측정이다. CPU 평균 약 2%만으로 메모리·색인·배포·SSE 여유를 판정하지 않는다. 이전 전 백업·스냅샷·고정 IP 복구를 확인하고, 이전 후 Spring API p95·`MemAvailable`·swap/OOM·PostgreSQL RSS/연결/WAL/디스크와 FastAPI/모델 RSS·cold load를 기록한다. 2GB 혼합 부하를 재현해 미통과하면 모델·배치·pool·색인 방식을 조정하고 재측정하며, 계속 실패하면 RAG 출시는 보류한다.

## 출시 차단 조건과 소유 경계

| 영역 | 현재 증거와 부족한 점 | 구현/판정 계약 |
|---|---|---|
| 인스턴스 이전 | 2GB/$12 이전은 2026-10-23 오후 예정이며 아직 실행 증거가 없다. | 서버 밖 PostgreSQL 논리 backup·복원, 정상 종료 스냅샷, 새 인스턴스 방화벽·고정 IP·공개 smoke·첫 백업과 rollback 경계를 [runbook](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/operations/runbooks/lightsail-2gb-migration.md)대로 검증한다. |
| DB 확장·복구 | 현재 운영 Compose는 PostGIS 이미지와 DB 320MiB 제한이다. pgvector·BM25 공존 이미지, migration, 복원 결과는 없다. | 인접 PostgreSQL major 업그레이드 없이 extension 버전을 고정하고 dump/restore·PostGIS 회귀·vector(384)·한국어 BM25·철회 재적용을 통과한다. 이미지 digest와 질의 계획을 기록한다. |
| AI 실행 자원 | FastAPI·질문 embedding·reranker를 같은 목표 2GB 호스트에 추가하는 Compose/메모리 예산과 실행 증거가 없다. | DB·Spring·Nginx·FastAPI/모델 동시 peak와 OS 여유를 실측하고 cold/warm 지연·동시 run을 검증한다. 문서 임베딩 배치는 온라인 피크와 직렬화한다. 내부 Docker 네트워크/TLS·전용 role 실패 테스트를 통과한다. Gemini LLM은 외부 API이며 호스트에 띄우지 않는다. |
| 후보·근거 품질 | BM25 20/vector 20→RRF 30→reranker 12는 설계값이다. | 같은 고정 corpus의 각 단계에서 gold 청크·source·장소 포함률과 탈락 이유를 측정한다. alias/동명이인·한국어 조사·부정·복합 질의를 분리 보고한다. 후보에 있었으나 cap 때문에 잃은 gold는 검색 실패로 합산하지 않는다. |
| 질의 계획 | 현재 SQL/본문 분기 외에 질문 유형별 lexical·dense 실행 경로와 외부 source adapter는 구현되지 않았다. | [QueryPlan](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/ai-rag/query-processing.md)의 route 정확도·불필요한 embedding 호출·fallback을 gold fixture로 측정한다. 첫 출시부터 SQL·lexical·dense·hybrid·SQL+검색을 모두 활성화하므로 각 경로의 구현·품질·2GB 부하를 함께 출시 게이트로 둔다. 외부 Wiki/API는 출처 권리·신선도·철회 계약 전까지 온라인에서 제외한다. |
| 출력 안전 | ID·출처 자격 검사는 의미상 claim 지지의 충분조건이 아니다. | 원천 offset/span과 원자적 claim의 관계·시간·부정 조건을 검사한다. 결정적 검사만으로 불명확하면 보류한다. 봉인셋 FACT·INTERPRETATION·PREFERENCE를 두 사람이 검수하고 의미 판정기는 오프라인부터 평가한다. provider 자유 텍스트를 SSE에 중계하지 않는다. |
| 버전·철회 | 온라인 run, 색인 active pointer, 설정 승격이 서로 다른 시점에 변한다. | run마다 corpus/config/revocation sequence를 고정하고 Spring 최종 저장 전 현재 공개 자격을 재검사한다. rollback은 철회 상태를 되돌리지 않는다. stale config 응답은 거부하고 같은 run의 기본 탐색으로 마친다. |
| 부하·비용 | 2GB 혼합 부하와 reranker 지연은 미실측이다. latency 목표는 아직 합의하지 않았다. | 먼저 단계별 warm/cold p50/p95/p99와 기준 API 지연을 계측한다. 이후 제품 사용성·품질·자원 증거에 따라 목표와 timeout을 정하고, DB 연결 포화·OOM/swap·디스크·RRF fallback 비율도 함께 평가한다. 무료 Gemini API의 실제 할당량·429·자동 유료 전환 차단을 검증하고, 별도 유료 자동 조사는 월 hard cap 없이는 비활성화한다. |
| 감독 trace | 비동기 버퍼 포화 시 trace 손실이 발생할 수 있다. Collector·trace backend의 AI 용량과 Langfuse 도입 필요성도 미검증이다. | 필수 감사·quota 원장은 트랜잭션에 남긴다. OTel/Grafana에서 실패 유형별 수집률·drop률·비용을 먼저 측정한다. Langfuse는 운영 서버 밖 제한 pilot으로 개인정보·보존·비용을 검증한다. 누락 case로 원인을 확정하지 않는다. |
| 격리 실험·승격 | Python runner·사람 승인·canary는 설계 상태다. | 운영 외 임시 DB에서 allowlist 한 축만 변경하고 CPU/RAM/시간/비용·egress를 제한한다. 승인 artifact hash와 배포 config hash를 대조한다. 2GB에서 병렬 canary가 불가능하면 순차 전환·차단 스위치로 별도 검증한다. |

## 구현 순서와 남는 결정

1. 운영 기준선을 기록하고 2GB/$12 새 인스턴스로 안전하게 이전한다. 이어 2GB 재현 환경을 만들며, 확장 이미지·복원·권한·혼합 부하 결과가 없으면 운영 DB 이미지를 RAG용으로 교체하지 않는다.
2. 공개 corpus→청크·384차원 vector·BM25→RRF→reranker→claim 검증→Spring 저장/SSE의 한 run을 구현한다. 300건 평가셋과 장애·철회 fixture를 통과한다.
3. stage별 구조화 trace·결정적 gold replay·규칙 기반 실패 분류를 구현한다. 운영 trace는 정답이 아니라 조사 신호로만 취급한다.
4. 격리 runner와 사람 승인, config hash 승격·rollback을 검증한다. 복합 사례의 선택적 LLM 조사는 이후 실제 조사 수요와 비용 한도가 확인될 때 추가한다.

품질 운영 기능은 `OTel 단계별 계측 → 결정적 평가·검토 큐(최대 3개월) → Grafana 집계·Discord/이메일 주간 요약 → 운영자 선택형 CLI 조사·격리 실험 → 사람 승인 배포` 순서로 구현한다. 각 앞 단계의 합성 실패·전송 유실·권한·만료 검증이 끝나야 다음 단계를 연다. 대화형 RAG 출시 게이트와 품질 개선 도구의 단계적 제공을 구분하고, 아직 구현되지 않은 검토 큐/요약을 운영 중인 기능으로 표시하지 않는다.

아직 선택·실측이 필요한 항목은 BM25 extension의 한국어 tokenizer/라이선스/메모리, reranker 모델·실행 위치·timeout 복귀율, FastAPI 비공개 토폴로지, 2GB 혼합 부하의 동시 run/DB pool/SSE 상한, 무료 Gemini API 모델·할당량·데이터 처리 고지, trace 저장량·수집률, 격리 runner 제공 방식이다. 각 결정은 [운영·평가 계획](operations-and-evaluation.md)의 측정 결과와 [평가 계약](evaluation-and-environment-tests.md)의 봉인셋 결과를 붙여 확정한다.
