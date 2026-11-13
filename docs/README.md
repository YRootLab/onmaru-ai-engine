# 문서 안내

이 문서는 저장소 문서의 진입점과 관리 원칙을 정리합니다. AI-RAG 설계는 [`ai-rag/README.md`](ai-rag/README.md), 아키텍처 의사결정은 [`decisions/README.md`](decisions/README.md)에서 시작하세요.

## 문서 지도

| 경로 | 내용 |
|---|---|
| [`ai-rag/`](ai-rag/README.md) | 여정 AI-RAG 제품·기술 설계, 계약, 평가 및 운영 준비 |
| [`decisions/`](decisions/README.md) | 이 저장소의 Architecture Decision Record(ADR) |
| [`ai-rag/diagrams/`](ai-rag/diagrams/README.md) | 아키텍처 다이어그램의 원본과 렌더링 방법 |
| [`ai-rag/reports/`](ai-rag/reports/) | Markdown 설계 자료에서 생성한 HTML·시각 보고서 |
| [`ai-rag/issue-planning/`](ai-rag/issue-planning/README.md) | AI-RAG 구현 작업 그래프와 GitHub Issue 분해 자료 |
| [`ai-rag/release-evidence/`](ai-rag/release-evidence/README.md) | 릴리스·성능 검증 evidence의 형식과 예시 |
| [`superpowers/specs/`](superpowers/specs/) | 개발 보조 작업에서 승인한 설계 문서 |

`README.md`가 저장소 전체의 런타임·배포 경계를 설명합니다. 현재 구현 여부를 확인할 때는 설계 문서만으로 판단하지 말고 코드, migration, OpenAPI 및 테스트를 함께 확인하세요. 과거 버전 문서와 생성 보고서는 현재 동작의 근거가 아닐 수 있습니다.

## 문서 소유권

- AI Engine 코드, AI corpus, 검색·생성·평가 설계는 이 저장소가 소유합니다.
- Spring 애플리케이션, 제품 공개 HTTP/SSE 계약, 운영 DB와 Lightsail 배포는 [OnMaru-backend](https://github.com/YRootLab/OnMaru-backend)가 소유합니다. AI 문서에서는 그 정본을 링크하고 복제본을 만들지 않습니다.
- 작업 상태는 저장소 지침에 따라 루트의 `handoff.md`, 미분류 후속 제안은 `improvements.md`, 실행 작업은 GitHub Issue에 기록합니다. `project-roadmap.md`는 장기 방향과 milestone만 다룹니다.

## 변경 원칙

1. 새 문서는 먼저 해당 주제의 정본이 이미 있는지 확인하고, 기존 문서에 보완할 수 있으면 새 문서를 만들지 않습니다.
2. 구조·프로토콜·데이터 경계가 바뀌면 ADR과 관련 계약·구현 문서를 함께 갱신합니다.
3. 릴리스 기록에는 이미지 tag, commit, 전체 digest 및 검증 범위를 기록합니다. 설계 계획과 실제 배포 증거를 구분합니다.
4. 문서를 이동하거나 이름을 바꾸면 저장소 전체의 Markdown 링크, 스크립트 경로, 생성 문서 참조를 함께 갱신합니다. 링크가 많으면 먼저 색인만 정리하고 경로는 유지합니다.
5. 비사소한 구현은 관련 Issue 및 acceptance criteria를 확인한 뒤 진행하고, PR 전후에 작업 로그·Issue·검증 결과를 대조합니다.

## ADR

아키텍처 경계, 저장소·프로토콜 선택, 핵심 검색 알고리즘, 보안 및 데이터 소유권에 장기 영향이 있는 결정을 [`decisions/`](decisions/)에 기록합니다. 단순 구현 세부나 일시적 작업 상태는 ADR로 만들지 않습니다. ADR 형식과 현재 목록은 [`decisions/README.md`](decisions/README.md)를 따릅니다.
