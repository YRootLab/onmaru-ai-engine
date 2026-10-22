# OnMaru AI Engine

Python/FastAPI AI engine for OnMaru. This repository will own query processing, retrieval, grounded generation, corpus indexing and the offline quality harness.

## Repository status

This is a local migration draft copied from `OnMaru-backend/docs/ai-rag/` on 2026-10-22. It is not yet the canonical published documentation: the source design is uncommitted in the backend workspace, and cross-repository references still need to be pinned to a reviewed backend commit. Do not treat this draft as deployed or production-ready.

The intended canonical design entry point is [`docs/ai-rag/README.md`](docs/ai-rag/README.md). After the backend source changes are reviewed and merged, this repository should receive the AI-owned docs and code, all backend links should point to immutable backend commits, and the backend copy should become a short pointer plus Spring implementation planning.

## Runtime and deployment boundary

The AI repository publishes a tested, immutable FastAPI container image. It does not own AWS credentials, the production `.env`, PostgreSQL volume, Nginx, or the Lightsail host. The existing backend repository owns the Lightsail Compose project and constrained deployment workflow. The target is to run Spring Boot, PostgreSQL, Nginx and one FastAPI container on the same existing Lightsail instance after its 2GB upgrade; no second instance is planned.

See [AI engine deployment and release model](docs/ai-rag/deployment-and-release-model.md). Current AWS Compose and deploy scripts do not yet include FastAPI, so this is a planned target pending staging resource, health, compatibility and rollback validation.
