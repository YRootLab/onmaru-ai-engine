import logging
import os
import sys
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from typing import Any, TextIO

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from onmaru_ai.api.plan_execute import PlanExecuteService, install_plan_execute
from onmaru_ai.composition import (
    create_production_plan_execute_service,
    get_spring_base_url,
    is_valid_http_origin,
)
from onmaru_ai.config.secrets import (
    SecretProvider,
    SecretRedactor,
    install_logging_redaction,
    provider_from_environment,
    validate_required_secrets,
)
from onmaru_ai.corpus.index import (
    CorpusIndexService,
    DeterministicEmbeddingProvider,
    FixedWordChunker,
)
from onmaru_ai.corpus.rest import install_corpus_rest
from onmaru_ai.corpus.sync import InMemoryCorpusStore
from onmaru_ai.observability import TelemetrySink, create_telemetry_sink, install_observability
from onmaru_ai.providers.gemini.adapter import GeminiAdapter
from onmaru_ai.providers.gemini.models import GeminiConfig, GeminiPricing
from onmaru_ai.providers.gemini.transport import HttpxGeminiTransport
from onmaru_ai.rag import RagActivationLog
from onmaru_ai.screenhanok.routes import install_screen_hanok_research
from onmaru_ai.screenhanok.service import ScreenHanokResearchService
from onmaru_ai.security import install_internal_auth
from onmaru_ai.security.internal_auth import RagEvidenceRetriever


def _rag_feature_enabled(environ: Mapping[str, str] | None = None) -> bool:
    source = os.environ if environ is None else environ
    return source.get("ONMARU_RAG_ENABLED", "").strip().lower() == "true"


def _screen_hanok_research_enabled(environ: Mapping[str, str] | None = None) -> bool:
    # ADR-0010 approves fully automated, unreviewed publishing once this is on -- keep it off
    # until a real Gemini API key and cost budget are configured for this environment.
    source = os.environ if environ is None else environ
    return source.get("ONMARU_SCREEN_HANOK_RESEARCH_ENABLED", "").strip().lower() == "true"


def _journey_gemini_enabled(environ: Mapping[str, str] | None = None) -> bool:
    source = os.environ if environ is None else environ
    return source.get("ONMARU_JOURNEY_GEMINI_ENABLED", "").strip().lower() == "true"


class _ApplicationStdoutHandler(logging.StreamHandler[TextIO]):
    """Dedicated stdout log handler for the onmaru_ai logger hierarchy."""


def configure_application_logging(
    level: int = logging.INFO,
    stream: TextIO | None = None,
) -> logging.Logger:
    app_logger = logging.getLogger("onmaru_ai")
    if app_logger.level == logging.NOTSET or app_logger.level > level:
        app_logger.setLevel(level)
    if not any(isinstance(handler, _ApplicationStdoutHandler) for handler in app_logger.handlers):
        handler = _ApplicationStdoutHandler(sys.stdout if stream is None else stream)
        handler.setLevel(level)
        handler.setFormatter(
            logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
        )
        app_logger.addHandler(handler)
    return app_logger


def create_app(
    secret_provider: SecretProvider | None = None,
    telemetry_sink: TelemetrySink | None = None,
    rag_activation_log: RagActivationLog | None = None,
    rag_retriever: RagEvidenceRetriever | None = None,
    corpus_store: InMemoryCorpusStore | None = None,
    corpus_index: CorpusIndexService | None = None,
    environ: Mapping[str, str] | None = None,
    plan_execute_service: PlanExecuteService | None = None,
    plan_execute_corpus_store: Any | None = None,
    plan_execute_catalog: tuple[Any, ...] | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> FastAPI:
    provider = secret_provider or provider_from_environment()
    secrets = validate_required_secrets(provider)
    app_logger = configure_application_logging()
    redactor = SecretRedactor(secrets)
    install_logging_redaction(redactor)
    install_logging_redaction(redactor, logger=app_logger)

    client = http_client or httpx.AsyncClient(timeout=httpx.Timeout(5.0))
    owns_client = http_client is None
    source_env = os.environ if environ is None else environ

    # Wire PostgreSQL RAG components if configured and not explicitly provided
    db_dsn = source_env.get("ONMARU_AI_DB_DSN") or source_env.get("ONMARU_DB_URL")
    if db_dsn and db_dsn.strip():
        from onmaru_ai.rag.postgres_activation import (
            PostgresRagActivationLog,
            PostgresRagEvidenceRetriever,
        )

        if rag_activation_log is None:
            rag_activation_log = PostgresRagActivationLog(db_dsn.strip())
        if rag_retriever is None:
            from onmaru_ai.embedding import (
                E5_SMALL_ONNX_INT8_384,
                EmbeddingService,
                load_e5_backend,
            )

            model_dir = source_env.get("ONMARU_E5_ONNX_DIR", "").strip()
            if not model_dir:
                raise ValueError("ONMARU_E5_ONNX_DIR is required for database retrieval")
            embed_backend = EmbeddingService(
                load_e5_backend(model_dir), profile=E5_SMALL_ONNX_INT8_384
            )

            def _embed_query(text: str) -> tuple[float, ...]:
                return embed_backend.embed_query(text)

            query_embedder = _embed_query
            query_profile_id = E5_SMALL_ONNX_INT8_384.profile_id
            rag_retriever = PostgresRagEvidenceRetriever(
                db_dsn.strip(),
                query_embedder=query_embedder,
                query_embedding_profile_id=query_profile_id,
            )

    if plan_execute_service is None and source_env.get(
        "ONMARU_DISABLE_DEFAULT_PLAN_EXECUTE", ""
    ).strip().lower() != "true":
        try:
            plan_execute_service = create_production_plan_execute_service(
                secret_provider=provider,
                http_client=client,
                environ=environ,
                corpus_store=plan_execute_corpus_store,
                catalog=plan_execute_catalog,
            )
        except ValueError:
            # Invalid origin configured; fail closed on /ready
            plan_execute_service = None

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        if owns_client:
            await client.aclose()

    app = FastAPI(title="OnMaru AI", lifespan=lifespan)
    app.state.plan_execute_service = plan_execute_service
    app.state.http_client = client
    install_observability(app, telemetry_sink or create_telemetry_sink())
    install_internal_auth(
        app,
        provider,
        rag_activation_log=rag_activation_log,
        rag_retriever=rag_retriever,
        rag_feature_enabled=_rag_feature_enabled(environ),
        journey_llm=_journey_llm(provider, environ, http_client=client),
    )
    install_plan_execute(app, provider, plan_execute_service)
    install_corpus_rest(
        app,
        provider,
        corpus_store or InMemoryCorpusStore(),
        corpus_index
        or CorpusIndexService(
            FixedWordChunker(max_words=120),
            DeterministicEmbeddingProvider(),
        ),
    )

    if _screen_hanok_research_enabled(environ):
        gemini_secret = provider.get("gemini.api-key")
        gemini_config = GeminiConfig(
            model_alias="screen-hanok-research",
            model_name=(os.environ if environ is None else environ).get(
                "ONMARU_GEMINI_MODEL_NAME"
            ) or "gemini-3.5-flash-lite",
            max_output_tokens=4096,
            pricing=GeminiPricing(input_micros_per_million=0, output_micros_per_million=0),
        )
        gemini_adapter = GeminiAdapter(
            gemini_config,
            HttpxGeminiTransport(client),
            api_key=gemini_secret.current,
            telemetry_sink=telemetry_sink or create_telemetry_sink(),
        )
        install_screen_hanok_research(app, provider, ScreenHanokResearchService(gemini_adapter))

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/ready")
    async def readiness() -> JSONResponse:
        # Check required secrets loadable
        try:
            for secret_name in ("internal-ai.service-token",):
                provider.get(secret_name)
        except Exception:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "missing_secrets"},
            )

        # Check Spring private base URL validity
        spring_url = get_spring_base_url(environ)
        if not is_valid_http_origin(spring_url):
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "invalid_spring_base_url"},
            )

        if _rag_feature_enabled(environ) and (
            rag_activation_log is None
            or not rag_activation_log.durable
            or rag_retriever is None
        ):
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "rag_runtime_unwired"},
            )

        # Check PlanExecuteService wired after feature-specific readiness checks.
        if plan_execute_service is None:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "plan_execute_service_unwired"},
            )

        # Check HTTP client ready
        if client.is_closed:
            return JSONResponse(
                status_code=503,
                content={"status": "not_ready", "reason": "http_client_closed"},
            )

        return JSONResponse(status_code=200, content={"status": "ready"})

    return app


def _journey_llm(
    secret_provider: SecretProvider,
    environ: Mapping[str, str] | None,
    http_client: httpx.AsyncClient | None = None,
) -> Any:
    if not _journey_gemini_enabled(environ):
        return None
    from onmaru_ai.journey_llm import JourneyLlmService

    gemini_secret = secret_provider.get("gemini.api-key")
    config = GeminiConfig(
        model_alias="journey-planner",
        model_name=(os.environ if environ is None else environ).get(
            "ONMARU_GEMINI_MODEL_NAME"
        ) or "gemini-3.5-flash-lite",
        max_output_tokens=2048,
        pricing=GeminiPricing(input_micros_per_million=0, output_micros_per_million=0),
    )
    return JourneyLlmService(
        GeminiAdapter(
            config,
            HttpxGeminiTransport(http_client),
            api_key=gemini_secret.current,
            telemetry_sink=create_telemetry_sink(),
        )
    )


app = create_app()
