# AI progress status design

## Goal

Show one changing line of truthful work status while an OnMaru journey answer is prepared. The browser receives status through Spring SSE. The final answer, cards, and citations come from the verified Spring snapshot.

## User experience

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

The current stage uses a calm indicator and one line. Stage changes use a short opacity transition, disabled when reduced motion is requested. Do not invent progress percentages or show stages that were skipped. A confirmed count may appear as `관련 자료 5개를 검토하고 있어요`; an unknown count uses the generic phrase. Do not show source names, retrieved text, draft claims, model tokens, or internal reasoning before final public eligibility and evidence validation.

## Event flow

1. The client sends the existing REST command with its idempotency key and subscribes to the existing run SSE stream.
2. Spring emits `run.stage` when a real stage starts or changes. The baseline stages are `INTERPRETING`, `RETRIEVING`, `GENERATING`, `VALIDATING`, and `PERSISTING`. The FE maps codes to localized messages; the server does not send arbitrary display text.
3. Spring and FastAPI use the existing private REST plan/execute contract first. During execute, FastAPI sends stage changes to a private, authenticated Spring progress endpoint. Each callback carries `runId`, approved `planHash`, stage code, per-run ordinal, and optional confirmed count. Spring accepts only a matching active run and plan, deduplicates repeated ordinals, and ignores late events after terminal state. Callback failure does not fail execution; Spring still emits its own `INTERPRETING`, `VALIDATING`, and `PERSISTING` stages and the final result. No callback contains unverified answer content.
4. Spring owns the ordered per-run event sequence and persists enough current state for reconnection. Once final validation and persistence succeed, Spring emits the terminal event; the FE loads the authoritative GET snapshot.
5. `run.text.delta`, if used, replays only already verified and saved narration. It is independent of status updates.

## Recovery and boundaries

- An SSE disconnect changes the line to `다시 연결하고 있어요`. Resume with `Last-Event-ID`; if replay is unavailable, read GET run and snapshot. Reconnection never starts another AI run.
- If a stage fails, display a concise retry/failure or verified fallback state. Do not leave a spinner running after a terminal failure.
- Progress event loss must not prevent final answer delivery. Spring can advance to the latest known stage; terminal snapshot remains authoritative.
- Progress events contain run ID, sequence, stage code, optional confirmed count, and timestamp. They contain no member ID, raw query, prompt, source text, or model output.

## Transport decision and benchmark

Ship the existing private REST plus Spring SSE path first. After measuring it, compare gRPC unary, server streaming, and bidirectional streaming for Spring–FastAPI only if the measurements justify a change. Record p50/p95 end-to-end latency, time to first status, stage delivery delay, concurrent connection and memory cost, failure/cancellation behavior, and operational complexity under the same workload. A transport change does not alter browser SSE or the verified snapshot contract. Bidirectional streaming is a candidate if repeated Spring↔FastAPI interaction during one run proves valuable; frequent browser interaction alone does not require it.

## Acceptance criteria

- A user sees actual stage transitions in one line, with no fabricated stage or percentage.
- A confirmed count is shown only when available; unverified source names and model output remain hidden.
- SSE replay and snapshot recovery restore the correct run without repeating execution.
- Terminal success replaces the status line with the verified answer; terminal failure ends the indicator.
- Stage codes and ordering are covered by a cross-service contract fixture when implemented.
