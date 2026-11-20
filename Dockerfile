# syntax=docker/dockerfile:1.7

FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS builder
WORKDIR /workspace

COPY pyproject.toml uv.lock ./
COPY src ./src

RUN uv sync --frozen --no-dev --no-editable

FROM ghcr.io/astral-sh/uv:python3.12-trixie-slim AS model-builder
WORKDIR /workspace

COPY pyproject.toml uv.lock ./
COPY src ./src
COPY scripts/export_e5_onnx.py ./scripts/export_e5_onnx.py

RUN uv sync --frozen --no-dev --group embedding-export --no-editable \
    && uv run --no-sync python scripts/export_e5_onnx.py --output /opt/onmaru/e5

FROM python:3.12-slim-trixie AS runner
WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && python -m pip install --no-cache-dir --upgrade pip "setuptools>=83.0.0" \
    && python -m pip uninstall --yes pip \
    && groupadd --system onmaru \
    && useradd --system --gid onmaru --home-dir /app --no-create-home onmaru

COPY --from=builder --chown=onmaru:onmaru /workspace/.venv /app/.venv
COPY --from=model-builder --chown=onmaru:onmaru /opt/onmaru/e5 /opt/onmaru/e5
COPY --chown=onmaru:onmaru scripts /app/scripts
COPY --chown=onmaru:onmaru migrations /app/migrations

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONUNBUFFERED=1 \
    ONMARU_AI_HOST=0.0.0.0 \
    ONMARU_AI_PORT=8000 \
    ONMARU_E5_ONNX_DIR=/opt/onmaru/e5

USER onmaru
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/ready', timeout=2).read()" || exit 1

CMD ["python", "-m", "uvicorn", "onmaru_ai.main:app", "--host", "0.0.0.0", "--port", "8000"]
