"""Production composition root for OnMaru AI Engine (W13/W0)."""

from __future__ import annotations

import logging
import re
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlsplit
from uuid import UUID

import httpx

from onmaru_ai.adapters.spring_place import SpringPlaceQueryAdapter
from onmaru_ai.api.plan_execute import (
    ExecutionResult,
    PlanExecuteService,
    TransportContext,
)
from onmaru_ai.config.secrets import SecretProvider
from onmaru_ai.contracts import (
    ApprovedQueryPlan,
    EvidenceSet,
    PlanProposal,
    SafeQueryRequest,
    ValidatedProposal,
    Versions,
)
from onmaru_ai.generation import EvidenceGenerator, GenerationInput
from onmaru_ai.orchestration import OrchestrationEngine
from onmaru_ai.progress import CallbackProgressSink
from onmaru_ai.query import CatalogEntry, QueryPlanner
from onmaru_ai.security.plan_validator import QueryGrant

logger = logging.getLogger(__name__)

DEFAULT_CATALOG_ENTRIES: tuple[CatalogEntry, ...] = (
    CatalogEntry(
        code="kr-11", kind="REGION", display_label="서울", synonyms=("서울시", "서울특별시")
    ),
    CatalogEntry(
        code="kr-26", kind="REGION", display_label="부산", synonyms=("부산시", "부산광역시")
    ),
    CatalogEntry(code="kr-45-jeonju", kind="REGION", display_label="전주", synonyms=("전주시",)),
    CatalogEntry(code="kr-41", kind="REGION", display_label="경기", synonyms=("경기도",)),
    CatalogEntry(code="kr-42", kind="REGION", display_label="강원", synonyms=("강원도",)),
    CatalogEntry(code="kr-28", kind="REGION", display_label="인천", synonyms=("인천시",)),
    CatalogEntry(code="kr-27", kind="REGION", display_label="대구", synonyms=("대구시",)),
    CatalogEntry(code="kr-30", kind="REGION", display_label="대전", synonyms=("대전시",)),
    CatalogEntry(code="kr-29", kind="REGION", display_label="광주", synonyms=("광주시",)),
    CatalogEntry(code="kr-31", kind="REGION", display_label="울산", synonyms=("울산시",)),
    CatalogEntry(code="kr-36", kind="REGION", display_label="세종", synonyms=("세종시",)),
    CatalogEntry(code="kr-43", kind="REGION", display_label="충북", synonyms=("충청북도",)),
    CatalogEntry(code="kr-44", kind="REGION", display_label="충남", synonyms=("충청남도",)),
    CatalogEntry(
        code="kr-45", kind="REGION", display_label="전북",
        synonyms=("전북특별자치도", "전라북도"),
    ),
    CatalogEntry(code="kr-46", kind="REGION", display_label="전남", synonyms=("전라남도",)),
    CatalogEntry(code="kr-47", kind="REGION", display_label="경북", synonyms=("경상북도",)),
    CatalogEntry(code="kr-48", kind="REGION", display_label="경남", synonyms=("경상남도",)),
    CatalogEntry(code="kr-50", kind="REGION", display_label="제주", synonyms=("제주도",)),
)

_SPRING_GRANT_REFERENCE = re.compile(r"qg_[A-Za-z0-9_-]{43}")


def bind_spring_grant_reference(
    grant_id: str,
    plan: ApprovedQueryPlan | None,
    now: datetime,
) -> QueryGrant | None:
    """Bind the opaque reference to the approved plan; Spring verifies issuance/use.

    AI Engine has no signing key or grant-store access. This local envelope only
    prevents cross-run/plan substitution; Spring's lookup endpoint authenticates,
    scopes, and consumes the reference against its persisted grant.
    """
    if plan is None or _SPRING_GRANT_REFERENCE.fullmatch(grant_id) is None:
        return None
    return QueryGrant(
        grant_id=grant_id,
        run_id=plan.run_id,
        plan_hash=plan.approved_plan_hash,
        filter_hash=plan.approved_filters.filter_hash,
        versions=plan.versions,
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(seconds=29),
    )


def is_valid_http_origin(url: str) -> bool:
    try:
        parsed = urlsplit(url)
        return (
            parsed.scheme in ("http", "https")
            and bool(parsed.netloc)
            and parsed.path in ("", "/")
            and not parsed.query
            and not parsed.fragment
        )
    except Exception:
        return False


def get_spring_base_url(environ: Mapping[str, str] | None = None) -> str:
    import os

    source = os.environ if environ is None else environ
    url = source.get("ONMARU_SPRING_BASE_URL", "").strip()
    if not url:
        return "http://staging-api:8080"
    return url.rstrip("/")


def default_verify_grant(
    grant_id: str,
    approved: ApprovedQueryPlan,
    now: datetime,
) -> QueryGrant | None:
    if not grant_id or len(grant_id) < 16 or len(grant_id) > 128:
        return None
    return QueryGrant(
        grant_id=grant_id,
        run_id=approved.run_id,
        plan_hash=approved.approved_plan_hash,
        filter_hash=approved.approved_filters.filter_hash,
        versions=approved.versions,
        issued_at=now - timedelta(seconds=1),
        expires_at=now + timedelta(seconds=29),
    )


class ProductionEvidenceGenerator:
    """Gemini generator adapter using exact corpus spans; facts remain registry-gated."""

    def __init__(
        self,
        provider: EvidenceGenerator,
        *,
        timeout_seconds: float = 12.0,
    ) -> None:
        self._provider = provider
        self._timeout_seconds = timeout_seconds

    async def generate(
        self,
        plan: ApprovedQueryPlan,
        evidence_set: EvidenceSet | None = None,
        lookup_outcome: Any | None = None,
        snapshot: Any | None = None,
        operation: str | None = None,
    ) -> ValidatedProposal | None:
        del lookup_outcome
        if evidence_set is None or snapshot is None:
            return None
        documents = []
        for source_id, source_revision in sorted(
            {(item.source_id, item.source_revision) for item in evidence_set.evidence}
        ):
            row = snapshot.connection.execute(
                """SELECT source_id, source_revision, revision_id, normalized_text
                     FROM ai.documents WHERE revision_id=%s AND source_id=%s
                       AND source_revision=%s AND eligibility_status='PUBLIC'""",
                (snapshot.versions.corpus_revision, source_id, source_revision),
            ).fetchone()
            if row is not None:
                documents.append({
                    "sourceId": row["source_id"],
                    "sourceRevision": row["source_revision"],
                    "corpusRevision": row["revision_id"],
                    "text": row["normalized_text"],
                })
        if len(documents) != len({(e.source_id, e.source_revision) for e in evidence_set.evidence}):
            return None
        if operation not in {"RECOMMEND", "EXPLAIN", "COMPARE", "REFINE"}:
            return None
        evidence_by_chunk = {item.chunk_id: item for item in evidence_set.evidence}
        try:
            fact_rows = snapshot.connection.execute(
                """SELECT f.fact_id, f.place_id, f.fact_text, f.kind, f.support_type,
                      f.time_scope, f.relation, f.chunk_id, f.start_offset, f.end_offset,
                      d.source_revision
                 FROM ai.reviewed_facts f
                 JOIN ai.chunks c USING (revision_id, chunk_id)
                 JOIN ai.documents d USING (revision_id, document_id)
                WHERE f.revision_id=%s AND f.review_status='APPROVED'
                  AND f.chunk_id = ANY(%s) AND d.source_id=f.place_id
                  AND d.eligibility_status='PUBLIC'
                    ORDER BY f.fact_id""",
                (
                    snapshot.versions.corpus_revision,
                    [UUID(item.chunk_id) for item in evidence_set.evidence],
                ),
            ).fetchall()
        except Exception:
            logger.warning("Reviewed fact registry unavailable; Gemini generation skipped")
            return None
        verified_facts = []
        for row in fact_rows:
            evidence = evidence_by_chunk.get(str(row["chunk_id"]))
            if (
                evidence is None
                or evidence.place_id != row["place_id"]
                or evidence.source_revision != row["source_revision"]
                or evidence.start_offset != row["start_offset"]
                or evidence.end_offset != row["end_offset"]
            ):
                continue
            verified_facts.append({
                "factId": row["fact_id"],
                "placeId": row["place_id"],
                "text": row["fact_text"],
                "kind": row["kind"],
                "evidenceIds": [evidence.evidence_id],
                "supportType": row["support_type"],
                "timeScope": row["time_scope"],
                "relation": row["relation"],
            })
        data = GenerationInput.model_validate({
            "operation": operation,
            "approvedPlan": plan,
            "evidenceSet": evidence_set,
            "currentVersions": snapshot.versions,
            "revokedSources": [
                {"sourceId": source_id, "sourceRevision": source_revision}
                for _source_type, source_id, source_revision in snapshot.revoked_sources
            ],
            "documents": documents,
            "verifiedFacts": verified_facts,
        })
        result = await self._provider.generate(data, timeout_seconds=self._timeout_seconds)
        return result.proposal


def create_production_plan_execute_service(
    *,
    secret_provider: SecretProvider,
    http_client: httpx.AsyncClient,
    environ: Mapping[str, str] | None = None,
    catalog: tuple[CatalogEntry, ...] | None = None,
    versions_factory: Callable[[], Versions] | None = None,
    corpus_store: Any | None = None,
) -> PlanExecuteService:
    spring_base_url = get_spring_base_url(environ)
    if not is_valid_http_origin(spring_base_url):
        raise ValueError(f"Invalid ONMARU_SPRING_BASE_URL origin: {spring_base_url}")

    def get_service_token() -> str:
        bundle = secret_provider.get("internal-ai.service-token")
        return bundle.current

    sql_adapter = SpringPlaceQueryAdapter(
        base_url=spring_base_url,
        service_token=get_service_token,
        client=http_client,
        timeout_seconds=2.0,
    )

    import os

    from onmaru_ai.storage.postgres import PostgresCorpusStore
    source_env = os.environ if environ is None else environ
    dsn = source_env.get("ONMARU_AI_DB_DSN") or source_env.get("ONMARU_DB_URL")
    store = corpus_store or (PostgresCorpusStore(dsn.strip()) if dsn and dsn.strip() else None)
    if store is None:
        raise ValueError("Plan/Execute requires an active Postgres corpus store")

    def active_versions() -> Versions:
        with store.snapshot() as snapshot:
            return snapshot.versions

    def load_catalog(snapshot: Any) -> tuple[CatalogEntry, ...]:
        rows = snapshot.connection.execute(
            """SELECT DISTINCT source_id AS place_id, title, region_code, category_code
                 FROM ai.documents WHERE revision_id=%s AND eligibility_status='PUBLIC'
                 ORDER BY title, place_id""", (snapshot.versions.corpus_revision,)
        ).fetchall()
        entries = list(DEFAULT_CATALOG_ENTRIES)
        for row in rows:
            region = str(row["region_code"]).strip().lower()
            category = str(row["category_code"]).strip().lower()
            # Normalize legacy ISO codes; Spring-specific city suffixes remain explicit
            # entries and are never guessed from a broad province code.
            if region.startswith("kr-"):
                region = region.upper().lower()
            entries.append(
                CatalogEntry(
                    code=str(row["place_id"]),
                    kind="PLACE",
                    display_label=str(row["title"]),
                    region_code=region or None,
                    category_code=category or None,
                )
            )
        return tuple(entries)

    # Issue #63: Wire real retrieval coordinator, reranker, and evidence selector
    # allowing HYBRID, SQL_PLUS_RETRIEVAL, LEXICAL_ONLY, DENSE_ONLY routes.
    from onmaru_ai.embedding import (
        GEMINI_EMBEDDING_384,
        EmbeddingService,
        GeminiEmbeddingBackend,
    )
    from onmaru_ai.retrieval.evidence import EvidenceSelector
    from onmaru_ai.retrieval.hybrid import HybridRetrievalCoordinator
    from onmaru_ai.retrieval.lexical import LexicalSearchAdapter, PostgresLexicalChunkRepository
    from onmaru_ai.retrieval.rerank import Reranker
    from onmaru_ai.retrieval.vector import VectorSearcher

    try:
        gemini_key = secret_provider.get("gemini.api-key").current
    except Exception as error:
        raise ValueError("Plan/Execute requires the Gemini API key") from error
    from onmaru_ai.observability import create_telemetry_sink
    from onmaru_ai.providers.gemini.adapter import GeminiAdapter
    from onmaru_ai.providers.gemini.models import GeminiConfig, GeminiPricing
    from onmaru_ai.providers.gemini.transport import HttpxGeminiTransport

    source_env = os.environ if environ is None else environ
    generation_provider = EvidenceGenerator(GeminiAdapter(
        GeminiConfig(
            model_alias="plan-execute-grounded",
            model_name=source_env.get("ONMARU_GEMINI_MODEL_NAME") or "gemini-3.5-flash-lite",
            max_output_tokens=4096,
            pricing=GeminiPricing(input_micros_per_million=0, output_micros_per_million=0),
        ),
        HttpxGeminiTransport(http_client),
        api_key=gemini_key,
        telemetry_sink=create_telemetry_sink(),
    ))
    generator = ProductionEvidenceGenerator(generation_provider)
    current_versions_factory = versions_factory or active_versions
    vector_searcher = VectorSearcher(EmbeddingService(
        GeminiEmbeddingBackend(gemini_key, task_type="RETRIEVAL_QUERY", timeout_seconds=2.5),
        profile=GEMINI_EMBEDDING_384,
    ))

    retrieval_coordinator = HybridRetrievalCoordinator(
        lexical_searcher=LexicalSearchAdapter(PostgresLexicalChunkRepository()),
        dense_searcher=vector_searcher,
    )
    reranker = Reranker()
    evidence_selector = EvidenceSelector()

    engine = OrchestrationEngine(
        sql_adapter=sql_adapter,
        retrieval_coordinator=retrieval_coordinator,
        reranker=reranker,
        evidence_selector=evidence_selector,
        generator=generator,
    )

    async def planner_func(request: SafeQueryRequest) -> PlanProposal:
        with store.snapshot() as snapshot:
            if request.versions != snapshot.versions:
                raise ValueError("VERSION_MISMATCH")
            selected_catalog = catalog if catalog is not None else load_catalog(snapshot)
            return QueryPlanner(catalog=selected_catalog).plan(request)

    async def executor_func(
        body: ApprovedQueryPlan,
        context: TransportContext | None = None,
    ) -> ExecutionResult:
        progress_sink = None
        if context is not None and context.progress_token:
            progress_sink = CallbackProgressSink(
                run_id=body.run_id,
                plan_hash=body.approved_plan_hash,
                receiver_base_url=spring_base_url,
                bearer_token=context.progress_token,
                client=http_client,
            )

        tp = (
            f"00-{context.trace_id}-{'1'*16}-01"
            if context is not None
            else "00-" + "0" * 32 + "-" + "0" * 16 + "-01"
        )
        with store.snapshot() as snapshot:
            if snapshot.versions != body.versions:
                raise ValueError("VERSION_MISMATCH")
            orch_result = await engine.execute_run(
                plan=body, snapshot=snapshot,
                progress_sink=progress_sink, traceparent=tp,
                operation=context.operation if context is not None else None,
            )

        proposal = orch_result.proposal
        evidence = orch_result.evidence


        return ExecutionResult.model_validate(
            {
                "schemaVersion": "ai-execute-result.v1",
                "runId": body.run_id,
                "planHash": body.approved_plan_hash,
                "versions": body.versions.model_dump(by_alias=True),
                "proposal": proposal,
                "evidence": evidence,
            }
        )

    def bind_grant_reference(
        grant_id: str, plan: ApprovedQueryPlan | None = None
    ) -> QueryGrant | None:
        return bind_spring_grant_reference(grant_id, plan, datetime.now(UTC))

    service = PlanExecuteService(
        planner=planner_func,
        executor=executor_func,
        current_versions=current_versions_factory,
        verify_grant=bind_grant_reference,
    )
    return service
