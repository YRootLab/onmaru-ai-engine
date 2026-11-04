# Improvements

Untriaged ideas captured during work. Triage each item into a local note, an existing Issue, a new Issue, or a verified completion.

## Inbox

- [ ] AI 엔진의 단계 이벤트를 현재 private REST 기반 통신으로 Spring에 전달한 뒤, Spring↔FastAPI 통신을 벤치마킹해 gRPC 양방향 스트리밍 도입 여부를 결정한다.
  - Context: 계획 승인 왕복과 단계별 상태 전달을 함께 측정한다. p50/p95 지연, 첫 상태 도착 시간, 동시 run당 메모리·연결 수, 실패·취소·재연결 복잡도와 운영 비용을 비교한다. 전환하더라도 브라우저 경계는 SSE와 확정 snapshot을 유지한다.
  - Suggested labels: needs-triage, area:adapter
  - Issue: none

## Resolved
