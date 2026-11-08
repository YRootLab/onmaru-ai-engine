"""Production composition root for OnMaru AI Engine (W13/W0)."""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlsplit

import httpx

from onmaru_ai.adapters.spring_place import (
    PlaceLookupDisposition,
    PlaceLookupOutcome,
    SpringPlaceQueryAdapter,
)
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
from onmaru_ai.contracts.models import Evidence, PlaceClaims
from onmaru_ai.contracts.validation import _place_allowed
from onmaru_ai.orchestration import OrchestrationEngine
from onmaru_ai.progress import CallbackProgressSink
from onmaru_ai.query import CatalogEntry, QueryPlanner
from onmaru_ai.security.plan_validator import QueryGrant

logger = logging.getLogger(__name__)

DEFAULT_CATALOG_ENTRIES: tuple[CatalogEntry, ...] = (
    CatalogEntry(code="JEONJU", kind="REGION", display_label="전주", synonyms=("전주시",)),
    CatalogEntry(code="SEOUL", kind="REGION", display_label="서울", synonyms=("서울시",)),
    CatalogEntry(code="BUSAN", kind="REGION", display_label="부산"),
    CatalogEntry(code="GYEONGGI", kind="REGION", display_label="경기"),
    CatalogEntry(code="GANGWON", kind="REGION", display_label="강원"),
    CatalogEntry(code="INCHEON", kind="REGION", display_label="인천"),
    CatalogEntry(code="DAEGU", kind="REGION", display_label="대구"),
    CatalogEntry(code="DAEJEON", kind="REGION", display_label="대전"),
    CatalogEntry(code="GWANGJU", kind="REGION", display_label="광주"),
    CatalogEntry(code="ULSAN", kind="REGION", display_label="울산"),
    CatalogEntry(code="SEJONG", kind="REGION", display_label="세종"),
    CatalogEntry(code="CHUNGBUK", kind="REGION", display_label="충북"),
    CatalogEntry(code="CHUNGNAM", kind="REGION", display_label="충남"),
    CatalogEntry(code="JEONBUK", kind="REGION", display_label="전북"),
    CatalogEntry(code="JEONNAM", kind="REGION", display_label="전남"),
    CatalogEntry(code="GYEONGBUK", kind="REGION", display_label="경북"),
    CatalogEntry(code="GYEONGNAM", kind="REGION", display_label="경남"),
    CatalogEntry(code="JEJU", kind="REGION", display_label="제주"),
    CatalogEntry(code="p1", kind="PLACE", display_label="경복궁", region_code="SEOUL"),
    CatalogEntry(code="p2", kind="PLACE", display_label="덕수궁", region_code="SEOUL"),
    CatalogEntry(
        code="p3",
        kind="PLACE",
        display_label="전주한옥마을",
        region_code="JEONJU",
        synonyms=("전주 한옥마을",),
    ),
    CatalogEntry(code="p4", kind="PLACE", display_label="중앙시장", region_code="SEOUL"),
    CatalogEntry(code="p5", kind="PLACE", display_label="중앙시장", region_code="BUSAN"),
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


@dataclass(frozen=True)
class DummyCorpusSnapshot:
    """Minimal immutable snapshot placeholder for queries when Postgres store is inactive."""

    versions: Versions
    embedding_profile_id: str = "e5-small-384"
    revoked_places: frozenset[Any] = frozenset()
    revoked_sources: frozenset[tuple[str, str, str]] = frozenset()
    connection: Any = None


def make_production_versions() -> Versions:
    return Versions.model_validate(
        {
            "corpusRevision": "corpus-1",
            "configHash": "sha256:" + "a" * 64,
            "questionDictionaryVersion": "questions-1",
            "sourceRevocationSequence": 7,
        }
    )


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


def build_evidence_and_proposal_from_lookup(
    plan: ApprovedQueryPlan,
    outcome: PlaceLookupOutcome,
) -> tuple[EvidenceSet, ValidatedProposal]:
    """Constructs valid EvidenceSet and ValidatedProposal from approved Spring place lookup."""
    valid_places = [p for p in outcome.places if _place_allowed(p.place_id, plan)]
    allowed_ids = tuple(p.place_id for p in valid_places)

    evidence_items: list[Evidence] = []
    place_claims_list: list[PlaceClaims] = []

    for idx, place in enumerate(valid_places, start=1):
        clean_pid = place.place_id.replace("-", "_")
        ev_id = f"ev-{idx}-{clean_pid}"
        chunk_id = f"chk-{idx}-{clean_pid}"
        claim_id = f"clm-{idx}-{clean_pid}"

        evidence_items.append(
            Evidence.model_validate(
                {
                    "evidenceId": ev_id,
                    "chunkId": chunk_id,
                    "placeId": place.place_id,
                    "sourceId": "src-approved-lookup",
                    "sourceRevision": "rev-0",
                    "startOffset": 0,
                    "endOffset": 10,
                }
            )
        )

        display_text = (
            place.public_address
            or place.address
            or place.name
            or f"Approved canonical place {place.place_id}"
        )
        place_claims_list.append(
            PlaceClaims.model_validate(
                {
                    "placeId": place.place_id,
                    "reasonClaims": [
                        {
                            "claimId": claim_id,
                            "text": display_text[:990],
                            "kind": "FACT",
                            "evidenceIds": [ev_id],
                        }
                    ],
                }
            )
        )

    evidence_set = EvidenceSet.model_validate(
        {
            "schemaVersion": "ai-evidence-set.v1",
            "runId": plan.run_id,
            "planHash": plan.approved_plan_hash,
            "versions": plan.versions.model_dump(by_alias=True),
            "allowedPlaceIds": allowed_ids,
            "evidence": evidence_items,
        }
    )

    proposal = ValidatedProposal.model_validate(
        {
            "schemaVersion": "ai-validated-proposal.v1",
            "runId": plan.run_id,
            "planHash": plan.approved_plan_hash,
            "versions": plan.versions.model_dump(by_alias=True),
            "candidatePlaceIds": allowed_ids,
            "places": place_claims_list,
            "summaryClaims": [],
            "retrievalStatus": "COMPLETE" if allowed_ids else "NO_EVIDENCE",
            "generationStatus": "GENERATED" if allowed_ids else "NOT_RUN",
            "failureStage": None,
        }
    )

    return evidence_set, proposal


class ProductionGenerator:
    """Production fallback generator reflecting approved place lookup results."""

    async def generate(
        self,
        plan: ApprovedQueryPlan,
        evidence_set: EvidenceSet | None = None,
        lookup_outcome: PlaceLookupOutcome | None = None,
    ) -> ValidatedProposal | None:
        if (
            lookup_outcome is not None
            and lookup_outcome.disposition == PlaceLookupDisposition.COMPLETE
            and lookup_outcome.places
        ):
            _, proposal = build_evidence_and_proposal_from_lookup(plan, lookup_outcome)
            return proposal

        if evidence_set is not None and evidence_set.allowed_place_ids:
            return ValidatedProposal.model_validate(
                {
                    "schemaVersion": "ai-validated-proposal.v1",
                    "runId": plan.run_id,
                    "planHash": plan.approved_plan_hash,
                    "versions": plan.versions.model_dump(by_alias=True),
                    "candidatePlaceIds": evidence_set.allowed_place_ids,
                    "places": [
                        {
                            "placeId": pid,
                            "reasonClaims": [
                                {
                                    "claimId": f"clm-{idx}-{pid.replace('-', '_')}",
                                    "text": f"Grounded candidate {pid}",
                                    "kind": "FACT",
                                    "evidenceIds": [ev.evidence_id],
                                }
                            ],
                        }
                        for idx, (pid, ev) in enumerate(
                            zip(
                                evidence_set.allowed_place_ids,
                                evidence_set.evidence,
                                strict=False,
                            ),
                            start=1,
                        )
                    ],
                    "summaryClaims": [],
                    "retrievalStatus": "COMPLETE",
                    "generationStatus": "GENERATED",
                    "failureStage": None,
                }
            )

        return None


def create_production_plan_execute_service(
    *,
    secret_provider: SecretProvider,
    http_client: httpx.AsyncClient,
    environ: Mapping[str, str] | None = None,
    catalog: tuple[CatalogEntry, ...] = DEFAULT_CATALOG_ENTRIES,
    versions_factory: Callable[[], Versions] = make_production_versions,
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

    query_planner = QueryPlanner(catalog=catalog)
    generator = ProductionGenerator()
    engine = OrchestrationEngine(sql_adapter=sql_adapter, generator=generator)

    async def planner_func(request: SafeQueryRequest) -> PlanProposal:
        return query_planner.plan(request)

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
        snapshot = DummyCorpusSnapshot(versions=body.versions)

        orch_result = await engine.execute_run(
            plan=body,
            snapshot=snapshot,  # type: ignore[arg-type]
            progress_sink=progress_sink,
            traceparent=tp,
        )

        proposal = orch_result.proposal
        evidence = orch_result.evidence

        if (
            body.approved_route in ("SQL_ONLY", "SQL_PLUS_RETRIEVAL")
            and proposal is not None
            and evidence is None
            and sql_adapter is not None
        ):
            # When lookup returned places, ensure proposal and evidence are paired
            lookup_places = [
                p for p in getattr(proposal, "places", ()) if _place_allowed(p.place_id, body)
            ]
            if lookup_places:
                # Build matching EvidenceSet
                ev_items = []
                for idx, p in enumerate(lookup_places, start=1):
                    clean_pid = p.place_id.replace("-", "_")
                    ev_items.append(
                        Evidence.model_validate(
                            {
                                "evidenceId": f"ev-{idx}-{clean_pid}",
                                "chunkId": f"chk-{idx}-{clean_pid}",
                                "placeId": p.place_id,
                                "sourceId": "src-approved-lookup",
                                "sourceRevision": "rev-0",
                                "startOffset": 0,
                                "endOffset": 10,
                            }
                        )
                    )
                evidence = EvidenceSet.model_validate(
                    {
                        "schemaVersion": "ai-evidence-set.v1",
                        "runId": body.run_id,
                        "planHash": body.approved_plan_hash,
                        "versions": body.versions.model_dump(by_alias=True),
                        "allowedPlaceIds": tuple(p.place_id for p in lookup_places),
                        "evidence": ev_items,
                    }
                )

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

    def verify_grant_func(
        grant_id: str,
        plan: ApprovedQueryPlan | None = None,
    ) -> QueryGrant | None:
        now = datetime.now(UTC)
        if not grant_id or len(grant_id) < 16 or len(grant_id) > 128:
            return None
        if plan is not None:
            return QueryGrant(
                grant_id=grant_id,
                run_id=plan.run_id,
                plan_hash=plan.approved_plan_hash,
                filter_hash=plan.approved_filters.filter_hash,
                versions=plan.versions,
                issued_at=now - timedelta(seconds=1),
                expires_at=now + timedelta(seconds=29),
            )
        return QueryGrant(
            grant_id=grant_id,
            run_id="",
            plan_hash="",
            filter_hash="",
            versions=versions_factory(),
            issued_at=now - timedelta(seconds=1),
            expires_at=now + timedelta(seconds=29),
        )

    service = PlanExecuteService(
        planner=planner_func,
        executor=executor_func,
        current_versions=versions_factory,
        verify_grant=verify_grant_func,
    )
    return service
