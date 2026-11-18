# AI-RAG 문서 분류와 읽는 순서

문서는 목적별 폴더에 둡니다. 진입점은 `README.md`이며, 각 주제의 자세한 정본과 현재 진단·이력의 구분은 해당 문서에서 확인합니다.

## 폴더 구조

```text
ai-rag/
├── README.md                         # 문서 색인과 현재 문서 기준
├── DOCUMENTATION.md                  # 이 분류·읽기 안내
├── product/                          # 제품 목표와 사용자 경험
├── architecture/                     # 온라인 파이프라인과 모듈 경계
├── integration/                      # Spring 연동 및 wire 계약
├── data/                              # corpus, ingestion, 검색 저장소
├── quality/                           # 근거, 평가, 품질 하네스
├── operations/                        # 배포, 관측, 보안, 출시 준비
├── history/                           # 버전별 과거 통합·운영 기록
├── reports/                           # 날짜가 붙은 분석·생성 보고서
├── diagrams/                          # 편집 가능한 목표 아키텍처 원본
├── schemas/                            # 기계 판독 계약
├── sql/                                # 운영자용 읽기 전용 SQL
├── issue-planning/                     # 작업 분해와 Issue 연결
└── release-evidence/                   # 릴리스 증거 형식과 산출물
```

## 먼저 읽을 순서

1. [문서 색인](README.md)에서 현재 정본과 구현/목표의 구분을 확인합니다.
2. [2026-11-17 카나리 역할 경계 진단 HTML](reports/2026-11-17-canary-role-boundary-review.html)에서 파이프라인 그림을 보고, 필요하면 [Markdown 원본](reports/2026-11-17-canary-role-boundary-review.md)에서 상세 source 링크를 확인합니다.
3. [제품 PRD](product/prd.md)에서 사용자 가치와 제품 인수 조건을 확인합니다.
4. [질문 처리 설계](architecture/query-processing.md)와 [모듈 경계](architecture/module-boundaries-and-pipelines.md)에서 목표 파이프라인을 확인합니다.
5. 필요한 계약·데이터·품질·운영 상세를 각 폴더에서 확인합니다.

## 문서 상태 원칙

- `product/`는 제품이 제공할 사용자 경험과 인수 조건을 정의합니다.
- `architecture/`, `integration/`, `data/`, `quality/`, `operations/`는 목표 기술 계약을 주제별로 나눕니다. 설계 문서만으로 구현 완료를 주장하지 않습니다.
- 날짜가 붙은 `reports/` 문서는 시점별 증거와 분석입니다. 최신 역할 경계 진단은 2026-11-17 보고서를 기준으로 읽고, 2026-10-21 HTML은 당시 목표 설계의 보관 스냅샷으로 취급합니다.
- `history/`는 과거 버전의 기록입니다. 현재 동작의 증거로 사용하지 않습니다.
- 제품 API, 실제 Spring 동작, 운영 데이터는 백엔드 저장소의 코드·계약·배포 증거와 대조합니다.
- 내부 Markdown 링크는 상대 경로로 작성하고 새 문서는 반드시 `README.md` 색인에 등록합니다.
