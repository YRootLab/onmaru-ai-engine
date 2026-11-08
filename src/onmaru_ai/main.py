import os
from collections.abc import AsyncIterator, Mapping
from contextlib import asynccontextmanager
from typing import Any

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
from onmaru_ai.rag import InMemoryRagActivationLog
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


def create_app(
    secret_provider: SecretProvider | None = None,
    telemetry_sink: TelemetrySink | None = None,
    rag_activation_log: InMemoryRagActivationLog | None = None,
    rag_retriever: RagEvidenceRetriever | None = None,
    corpus_store: InMemoryCorpusStore | None = None,
    corpus_index: CorpusIndexService | None = None,
    environ: Mapping[str, str] | None = None,
    plan_execute_service: PlanExecuteService | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> FastAPI:
    provider = secret_provider or provider_from_environment()
    secrets = validate_required_secrets(provider)
    install_logging_redaction(SecretRedactor(secrets))

    client = http_client or httpx.AsyncClient(timeout=httpx.Timeout(5.0))
    owns_client = http_client is None

    if plan_execute_service is None:
        source_env = os.environ if environ is None else environ
        if source_env.get("ONMARU_DISABLE_DEFAULT_PLAN_EXECUTE", "").strip().lower() != "true":
            try:
                plan_execute_service = create_production_plan_execute_service(
                    secret_provider=provider,
                    http_client=client,
                    environ=environ,
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
        journey_llm=_journey_llm(provider, environ),
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
                "ONMARU_GEMINI_MODEL_NAME", "gemini-2.5-flash"
            ),
            max_output_tokens=4096,
            pricing=GeminiPricing(input_micros_per_million=0, output_micros_per_million=0),
        )
        gemini_adapter = GeminiAdapter(
            gemini_config,
            HttpxGeminiTransport(),
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

        # Check PlanExecuteService wired
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


def _journey_llm(secret_provider: SecretProvider, environ: Mapping[str, str] | None) -> Any:
    if not _journey_gemini_enabled(environ):
        return None
    from onmaru_ai.journey_llm import JourneyLlmService

    gemini_secret = secret_provider.get("gemini.api-key")
    config = GeminiConfig(
        model_alias="journey-planner",
        model_name=(os.environ if environ is None else environ).get(
            "ONMARU_GEMINI_MODEL_NAME", "gemini-2.5-flash"
        ),
        max_output_tokens=2048,
        pricing=GeminiPricing(input_micros_per_million=0, output_micros_per_million=0),
    )
    return JourneyLlmService(
        GeminiAdapter(
            config,
            HttpxGeminiTransport(),
            api_key=gemini_secret.current,
            telemetry_sink=create_telemetry_sink(),
        )
    )


app = create_app()
