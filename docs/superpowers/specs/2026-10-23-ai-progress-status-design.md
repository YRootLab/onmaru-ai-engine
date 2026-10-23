# AI Engine progress event pipeline

## Goal

Emit coarse, truthful progress events from the FastAPI AI-RAG pipeline so Spring can relay them through its existing `run.stage` SSE stream. This repository owns event production and its internal transport adapter. Spring owns SSE, reconnection, and the final verified snapshot. The frontend owns presentation; neither is implemented here.

## Downstream display reference

```text
User question
┌──────────────────────────────────────────────┐
│ ◌ 조건에 맞는 장소를 찾고 있어요             │
│   검색 → 근거 확인 → 답변 작성 → 최종 확인     │
└──────────────────────────────────────────────┘

After completion
┌──────────────────────────────────────────────┐
│ 검증된 답변                                  │
│ 장소 카드 · 출처                             │
└──────────────────────────────────────────────┘
```

This diagram illustrates how downstream clients may display the events; it is not a frontend task in this repository. The AI Engine emits stage codes, not Korean UI text or progress percentages. It does not enumerate searched documents, source names, retrieved text, draft claims, model tokens, or internal reasoning. Skipped stages produce no event.

## Event flow

1. Spring sends the existing approved plan to FastAPI `execute`. Planning and approval remain separate from execution.
2. The AI Engine publishes an event when it actually enters one of these coarse stages: `PREPARING_INPUT`, `RETRIEVING`, `SELECTING_EVIDENCE`, `GENERATING`, `CHECKING_OUTPUT`. Each event has `runId`, approved `planHash`, stage code, and a monotonically increasing AI ordinal. It has no arbitrary display text or unverified content. Route-specific stages that do not run are omitted.
3. A transport-independent `ProgressSink` receives these events from the pipeline. The initial private REST adapter forwards them to a private authenticated Spring progress endpoint. Callback failure is recorded but does not fail the answer; duplicate callbacks are safe through the ordinal and run identity. If delivery is delayed, later events must not overwrite a newer stage.
4. The AI Engine emits its final execute result through the existing contract. Spring maps AI stages to its `run.stage` events and owns terminal state, SSE sequence, replay, and snapshot. Spring's final validation and persistence are Spring-owned stages, not AI events.

## Failure and ownership boundaries

- A progress delivery failure does not retry the model or change the execute result. The adapter may retry the same event within a bounded deadline using the same ordinal.
- A pipeline failure returns its existing typed error or fallback result. The AI Engine does not claim a later stage completed when it did not run.
- Spring handles SSE disconnection, replay, terminal state, and snapshot recovery. Those behaviors are external contract requirements, not implementation tasks here.
- Progress events contain no member ID, raw query, prompt, source text, or model output. An optional count is deferred until a stable, non-sensitive count contract is agreed with Spring.

## Transport decision and benchmark

Build the AI progress pipeline against the existing private REST plan/execute path first. After measuring it, compare gRPC unary, server streaming, and bidirectional streaming for Spring–FastAPI only if the measurements justify a change. Record p50/p95 end-to-end latency, time to first status, stage delivery delay, concurrent connection and memory cost, failure/cancellation behavior, and operational complexity under the same workload. A transport change does not alter the progress event semantics or Spring's SSE and snapshot contract.

## Acceptance criteria

- The AI Engine emits only stages actually entered by the selected route, in monotonic AI ordinal order.
- Every event is tied to the approved run and plan; retries cannot create a new run or regress the stage.
- Event delivery failure does not fail execution or expose sensitive content.
- The AI Engine's execute result remains authoritative for its work; Spring remains authoritative for final public validation and snapshot.
- Event schema and route-specific stage ordering have contract fixtures shared with Spring when the integration is implemented.
