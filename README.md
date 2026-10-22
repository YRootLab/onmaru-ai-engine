# OnMaru AI Engine

Python/FastAPI AI engine for OnMaru. This repository will own query processing, retrieval, grounded generation, corpus indexing and the offline quality harness.

## Repository status

The AI-RAG documentation was copied from `OnMaru-backend/docs/ai-rag/` on 2026-10-22 and published on the `docs/ai-rag-transfer` review branch (commit `00847c174043ccf6d542a6ac15c595556ce8da3f`). It is not yet the canonical default-branch documentation. Backend-owned cross-references still need to be pinned to reviewed backend commits. This migration does not imply that the FastAPI runtime or AWS deployment has moved.

The intended canonical design entry point is [`docs/ai-rag/README.md`](docs/ai-rag/README.md). Once this review branch is merged, it becomes the AI design source of truth. The backend copy is now a short pointer plus Spring implementation planning. Backend links will be pinned to immutable commits after the corresponding backend planning changes are reviewed and merged.

## Runtime and deployment boundary

The AI repository publishes a tested, immutable FastAPI container image. It does not own AWS credentials, the production `.env`, PostgreSQL volume, Nginx, or the Lightsail host. The existing backend repository owns the Lightsail Compose project and constrained deployment workflow. The target is to run Spring Boot, PostgreSQL, Nginx and one FastAPI container on the same existing Lightsail instance after its 2GB upgrade; no second instance is planned.

See [AI engine deployment and release model](docs/ai-rag/deployment-and-release-model.md). Current AWS Compose and deploy scripts do not yet include FastAPI, so this is a planned target pending staging resource, health, compatibility and rollback validation.
