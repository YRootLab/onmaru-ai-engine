# Repository guidance

## Sources of truth

- `README.md` describes the current runtime and deployment boundary.
- `docs/ai-rag/README.md` is the entry point for AI-RAG design; treat generated reports and diagrams as outputs of their sources.
- GitHub Issues track triaged, actionable work. `project-roadmap.md` holds long-term direction and milestones only.
- `handoff.md` captures the current session. `improvements.md` captures untriaged follow-up ideas. Neither is a second backlog.

## Work tracking

- Before non-trivial implementation, search for a related GitHub Issue or create one with context and acceptance criteria. Link it in `handoff.md` and align the work branch.
- Record ad hoc requests immediately in `handoff.md` when they affect the current session, or `improvements.md` when they are follow-up ideas. Triage them later: keep locally, link an existing Issue, create an Issue, or remove after verifying completion.
- Before opening a PR and again before merging it, use `cleaning-work-logs` or perform its equivalent scan and reconciliation of branch, logs, Issues, PR, and verification results.
- Every PR references its Issue. Use an auto-close keyword only when merging that PR into its target completes the Issue. Check acceptance criteria and merge state before closing an Issue.
- Review destructive repository and GitHub changes before execution. Verify changed files and relevant behavior with fresh evidence.

## Git Flow branch policy

- Production branch: `main`, matching the current remote default and image publishing workflow.
- Integration branch: `develop`. Merge `feature/*`, `fix/*`, and `docs/*` into `develop` by PR.
- Create `release/*` from `develop`; merge release branches into `main` by PR. Routine releases do not require a `main` to `develop` back merge.
- Create emergency `hotfix/*` from `main` and merge the fix into both `main` and `develop`.
- Do not push directly to shared `main` or `develop` branches. Require passing CI and review before merge; protect against force pushes and branch deletion. Delete short-lived branches after merge.
- Create semantic version tags such as `v0.3.2` from `main` only. Rebuild and verify generated artifacts before release. Keep workflow permissions minimal and avoid workflow loops.
- `develop` exists and receives documentation PRs. Branch rules and release automation still require separate configuration. The current CI publishes a commit image on `main`; coordinate any further Git Flow activation with that workflow.
