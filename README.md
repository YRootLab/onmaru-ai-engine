# OnMaru AI Engine

OnMaru의 Python/FastAPI AI 엔진 저장소입니다. 자연어 질문 처리, 검색, 근거 기반 생성, 공개 corpus 색인, 비동기 품질 harness가 목표 범위입니다.

## Repository status

AI-RAG 설계 문서·다이어그램·HTML 보고서는 2026-10-22 이 저장소로 이전했습니다. 백엔드가 소유하는 문서 링크는 해당 변경의 검토·병합 후 불변 commit으로 고정할 예정입니다. FastAPI runtime은 백엔드의 기존 baseline을 이 저장소로 이동하는 중이며, AWS 운영 배포가 이전되었다는 뜻은 아닙니다.

정본 설계 진입점은 [`docs/ai-rag/README.md`](docs/ai-rag/README.md)입니다. 백엔드 저장소에는 짧은 진입 안내와 Spring 구현 계획만 남깁니다.

## Runtime and deployment boundary

AI 저장소는 검증된 FastAPI container image를 발행합니다. AWS credential, 운영 `.env`, PostgreSQL volume, Nginx, Lightsail host는 소유하지 않습니다. 기존 백엔드 저장소가 Lightsail Compose와 제한 배포 workflow를 소유합니다. 목표는 기존 Lightsail을 2GB로 확장한 뒤 Spring Boot, PostgreSQL, Nginx, FastAPI를 같은 인스턴스에서 실행하는 것이며 두 번째 인스턴스는 계획하지 않았습니다.

현재 이동 중인 FastAPI 코드는 기존 16차원 결정적 임베딩·메모리 검색 baseline입니다. 이 코드를 384차원 pgvector, BM25, hybrid ranking이 구현된 것으로 간주하지 않습니다. 실제 운영 배포 전에는 코드·DB migration·독립 CI·digest 기반 배포 및 공존 검증이 필요합니다. 자세한 목표는 [배포/릴리스 설계](docs/ai-rag/deployment-and-release-model.md)를 참고하세요.

## 개발 환경

Python 3.12와 `uv`를 사용합니다.

```bash
uv sync --frozen --all-groups
uv run pytest
uv run ruff check
uv run mypy
uv run uvicorn onmaru_ai.main:app --reload --port 8001
```

Offline AI 평가:

```bash
uv run python scripts/run-ai-evals \
  --input evals/journey-held-out-v1.json \
  --output /tmp/onmaru-ai-eval-report.json
```
