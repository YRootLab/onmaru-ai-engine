# AI progress event contract proposal

> Planning handoff. This repository owns the FastAPI event producer. OnMaru BE owns the public Journey OpenAPI, SSE schema, run snapshot, and Spring receiver. No endpoint in this document has been implemented.

## Boundaries

| Boundary | Owner | Contract |
| --- | --- | --- |
| FastAPI pipeline → Spring | AI produces; Spring receives | Private `POST /internal/v1/ai/runs/{runId}/progress` proposal |
| Spring → browser | BE | Existing `GET /api/v1/explorations/{explorationId}/runs/{runId}/events` SSE |
| Browser recovery | BE | Existing GET run and exploration snapshot |

The browser never calls FastAPI. The command remains REST, progress remains `run.stage` SSE, and the snapshot remains the final result.

## Private AI progress callback

FastAPI reports a stage only after the pipeline actually enters it. Proposed body:

```json
{
  "schemaVersion": "ai-progress.v1",
  "runId": "45e6a7f5-31bc-469d-9e30-6f510a1dc497",
  "planHash": "sha256:approved-plan-hash",
  "ordinal": 3,
  "stage": "SELECTING_EVIDENCE"
}
```

`ordinal` starts at 1 and increases within a run. `stage` is one of `PREPARING_INPUT`, `RETRIEVING`, `SELECTING_EVIDENCE`, `GENERATING`, `CHECKING_OUTPUT`. A route emits only stages it enters. The payload contains no raw question, member ID, document title, source body, prompt, draft answer, or model reasoning.

Spring supplies a short-lived callback bearer token in the execute request, scoped to `journey.progress.write`, this run, and the Spring receiver audience. Spring validates token, active run, and approved plan hash. Repeating the same ordinal and stage is a no-op; an older ordinal cannot regress state; a conflicting same-ordinal event or wrong plan is rejected. Events after terminal state are ignored. Callback delivery failure is observable but does not fail AI execution or start another model run.

## Public SSE proposal for BE

| AI stage | Public `run.stage` |
| --- | --- |
| `PREPARING_INPUT` | `INTERPRETING` |
| `RETRIEVING` | `RETRIEVING` |
| `SELECTING_EVIDENCE` | `SELECTING_EVIDENCE` |
| `GENERATING` | `GENERATING` |
| `CHECKING_OUTPUT` | `VALIDATING` |

Spring can also emit its own `INTERPRETING`, `VALIDATING`, and `PERSISTING` stages and suppresses repeated public stages. `SELECTING_EVIDENCE` and `GENERATING` extend the existing public enum. BE should include them in Journey OpenAPI, SSE JSON Schema, GET run snapshot schema, and fixtures under its planned `1.3` contract. Older clients need a fixture proving they show a generic busy message for an unknown stage before rollout.

Illustrative parsed SSE frame:

```json
{
  "id": "8",
  "event": "run.stage",
  "data": {
    "schemaVersion": "1.3",
    "runId": "45e6a7f5-31bc-469d-9e30-6f510a1dc497",
    "sequence": 8,
    "status": "RUNNING",
    "stage": "SELECTING_EVIDENCE"
  }
}
```

Spring assigns the SSE `sequence`; the AI `ordinal` never reaches the browser. The browser maps codes to localized one-line messages. `Last-Event-ID` replay, reset, GET snapshot recovery, and terminal behavior remain BE-owned. `run.text.delta` remains separate and contains only narration that has already been verified and saved.

## Contract review

BE must align the callback path, token claims, and error responses with its internal service authentication policy. Contract fixtures should cover skipped stages, duplicate/out-of-order callbacks, wrong run/plan, late callback after terminal, callback failure with successful execute, SSE replay/reset, and older client fallback. Keep private REST plan/execute as the baseline and benchmark gRPC variants after measuring it.
