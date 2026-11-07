# AI-RAG 구현 이슈 실행 계획

> 상태: 설계와 작업 분해 완료, 엔진 구현 전. [Root Issue #3](https://github.com/YRootLab/onmaru-ai-engine/issues/3) 아래 23개 하위 이슈를 생성했다. 제목의 `W0`~`W22`는 안정적인 작업 ID이며 Wave 번호와 다르다.

## 지금까지 완료한 작업

- 기존 AI-RAG 설계를 AI 엔진 소유 범위로 나누고 Spring·FE·운영 인프라의 소유 경계를 명시했다.
- FastAPI → Spring 진행 이벤트 초안을 정의했다. AI는 실행한 단계만 내부 callback으로 알리고, Spring이 공개 `run.stage` SSE와 확정 snapshot을 소유한다. 세부 계약은 [진행 이벤트 계약](../progress-event-contract.md)에 있다.
- 23개 구현 이슈의 목표, 범위, 선행 작업, 예상 수정 경로, 인수 기준, 검증 방법을 [작업 그래프](work-graph.json)에 기록했다. 실제 GitHub 번호는 [생성 목록](created-issues.json)에 있다.
- Root/Child의 GitHub Sub-Issue와 blocked-by 관계를 연결하고, 제목에 작업 ID, 라벨에 `track:*`와 `area:*`를 붙였다.

## 구현할 세 파이프라인

1. **공개 Corpus 준비:** Spring의 공개 projection·권리·철회 manifest를 검증하고 본문을 정규화·청킹한다. 같은 revision의 passage embedding(384차원)과 한국어 BM25를 구축한 후 원자적으로 active revision을 전환한다. 철회는 검색보다 먼저 차단한다. 관련 이슈: W1–W6.
2. **온라인 질의와 답변:** Spring이 인증·비식별화한 요청을 AI에 전달한다. AI는 질문을 정규화해 다섯 route 중 하나를 제안하고, Spring이 승인한 불변 plan만 실행한다. 필요한 경로에서 제한된 Spring 정형 조회, BM25/vector 검색, RRF, reranker, 근거 선택을 거쳐 근거가 뒷받침하는 claim만 proposal로 반환한다. Spring이 공개 상태와 근거를 최종 검증·저장한 뒤 SSE와 snapshot을 클라이언트에 제공한다. 실패 시 같은 run에서 허용된 기본 탐색 또는 명시적 실패로 종료한다. 관련 이슈: W0, W7–W14.
3. **관측·평가·개선:** 단계별 OTel trace와 낮은 카디널리티 metric을 수집하고, 개발 200문항·봉인 100문항의 gold 데이터로 route·검색·근거 품질을 재현 평가한다. 실패 사례를 비동기 검토 큐에 모아 집계·주간 요약으로 알린다. 원인 조사와 격리 실험, 설정 승격은 운영자 선택과 승인을 거친다. AI 이미지와 staging 혼합 부하 증거로 출시 게이트를 판정한다. 관련 이슈: W15–W22.

## 병렬 진행 순서

| Wave | 작업 ID | 합류 조건 |
| ---: | --- | --- |
| 0 | W0 | AI↔Spring 버전형 계약과 fixture 확정 |
| 1 | W1, W3, W7, W8, W12, W15, W16 | Corpus·온라인·품질 모듈의 독립 착수 |
| 2 | W2, W6, W9, W14, W17, W22 | 전처리·권한·진행 이벤트·평가 데이터 연결 |
| 3 | W4, W5, W18 | 같은 revision의 vector/BM25와 실패 큐 |
| 4 | W10, W19, W20 | hybrid 검색과 품질 운영 경계 |
| 5 | W11 | 근거 재정렬·출처 다양성 |
| 6 | W13 | 다섯 route 통합 실행·fallback |
| 7 | W21 | 봉인 평가·2GB 공존·출시 증거 |

같은 Wave의 이슈는 병렬 작업 후보이며, 선행 이슈가 완료되어야 착수할 수 있다. 세부 의존성은 [Root Issue #3](https://github.com/YRootLab/onmaru-ai-engine/issues/3)의 Mermaid 그래프와 GitHub blocked-by 관계를 따른다.

## 저장소 경계와 현재 상태

- 이 저장소는 AI의 내부 계약·Corpus·검색·생성·진행 이벤트 생산·품질 하네스를 구현한다.
- OnMaru BE는 회원·대화·정형 조회·plan 승인·최종 검증·공개 API/SSE·DB 운영을 맡는다. FE는 단계별 한 줄 상태를 표시한다.
- Spring↔FastAPI plan/execute는 private REST를 기준선으로 둔다. gRPC unary/bidirectional은 실제 병목과 운영 비용을 측정한 뒤 별도 판단한다.
- 이 문서와 이슈는 **계획 산출물**이다. 23개 구현 이슈의 기능이 현재 코드에 완성됐다는 뜻은 아니다.
