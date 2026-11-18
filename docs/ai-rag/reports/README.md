# AI-RAG 보고서

보고서에는 기준 시점과 용도를 표시합니다. 운영 구현 여부는 보고서만으로 판단하지 말고 해당 시점의 source, 배포 digest, request/log artifact와 함께 확인합니다.

## 최신 역할 경계 진단 · 2026-11-17

- [HTML 보고서](2026-11-17-canary-role-boundary-review.html): 파이프라인 비교 그림과 읽기용 전체 진단. 단일 정적 파일이며 외부 스크립트가 필요하지 않습니다.
- [Markdown 원본](2026-11-17-canary-role-boundary-review.md): 변경 이력과 source 링크를 검토하거나 편집할 때 사용합니다.
- 기준: AI Engine `4633dc7a8d0262c753338d547a5feb5ed4396c6f`, backend `develop` `39f2db07b896dafd035aec0dbadd1e96f3d44028`. 운영 host에서 직접 수집한 trace/raw request는 분석 범위에 포함하지 않았습니다.

## 당시 목표 아키텍처 스냅샷 · 2026-10-21

- [시스템 브리핑 HTML](2026-10-21-system-briefing.html): 목표 시스템 구조를 설명하는 당시 생성 산출물입니다. 현재 배포 상태나 카나리 실행 증거로 사용하지 않습니다.
- 새 설계 브리핑은 이 파일을 덮어쓰지 말고 새 날짜 파일로 생성합니다.

상위 색인: [AI-RAG 문서 안내](../README.md).
