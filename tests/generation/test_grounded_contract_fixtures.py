"""Grounding contract checks shared by the fixed W0 fixtures and the Gemini generation path.

The fixed fixtures in ``tests/contracts/fixtures`` are the contract authority. Gemini output
is only accepted when it reproduces the same claim -> evidence -> place binding, and the
production lookup builder must produce the same binding without any model involved.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest

from onmaru_ai.adapters.spring_place import (
    CanonicalPlaceProjection,
    PlaceLookupDisposition,
    PlaceLookupOutcome,
)
from onmaru_ai.composition import build_evidence_and_proposal_from_lookup
from onmaru_ai.contracts import (
    ApprovedQueryPlan,
    ContractViolation,
    EvidenceSet,
    ValidatedProposal,
    validate_artifact,
)
from onmaru_ai.generation import EvidenceGenerator, GenerationInput
from onmaru_ai.observability import InMemoryTelemetrySink
from onmaru_ai.providers.gemini.adapter import GeminiAdapter
from onmaru_ai.providers.gemini.models import (
    GeminiConfig,
    GeminiPricing,
    GeminiTransportRequest,
    GeminiTransportResponse,
)

CONTRACT_FIXTURES = Path(__file__).parents[1] / "contracts" / "fixtures"
FACT_TEXT = "차분하게 둘러볼 수 있는 한옥입니다."


def contract_payload(name: str) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((CONTRACT_FIXTURES / f"{name}.json").read_text())
    payload: dict[str, Any] = data["payload"]
    return payload


class FixedOutputTransport:
    def __init__(self, output: object) -> None:
        self.output = output
        self.requests: list[GeminiTransportRequest] = []

    async def generate(self, request: GeminiTransportRequest) -> GeminiTransportResponse:
        self.requests.append(request)
        return GeminiTransportResponse(
            200,
            {"candidates": [{"content": {"parts": [{"text": json.dumps(self.output)}]}}]},
        )

    async def stream(
        self, request: GeminiTransportRequest
    ) -> AsyncIterator[GeminiTransportResponse]:
        raise AssertionError("grounded generation must not stream")
        yield  # pragma: no cover


def assert_claims_bound_to_same_place(
    proposal: ValidatedProposal, evidence_set: EvidenceSet
) -> None:
    place_by_evidence = {item.evidence_id: item.place_id for item in evidence_set.evidence}
    for place in proposal.places:
        assert place.reason_claims, "every place needs at least one reason claim"
        for claim in place.reason_claims:
            assert claim.evidence_ids, "claims must cite evidence"
            for evidence_id in claim.evidence_ids:
                assert place_by_evidence[evidence_id] == place.place_id


def gemini_generation_input() -> dict[str, Any]:
    """Fixed plan + evidence, with a source document aligned to the fixed fact text.

    The fixed evidence span is re-derived to cover the whole fact so the span check in the
    generator can compare exact text; plan, evidence IDs, place IDs and versions are unchanged.
    """
    plan = contract_payload("accepted-approved-hybrid")
    evidence = contract_payload("accepted-evidenceset")
    evidence["evidence"][0]["endOffset"] = len(FACT_TEXT)
    return {
        "operation": "EXPLAIN",
        "approvedPlan": plan,
        "evidenceSet": evidence,
        "currentVersions": plan["versions"],
        "revokedSources": [],
        "documents": [
            {
                "sourceId": evidence["evidence"][0]["sourceId"],
                "sourceRevision": evidence["evidence"][0]["sourceRevision"],
                "corpusRevision": plan["versions"]["corpusRevision"],
                "text": FACT_TEXT,
            }
        ],
        "verifiedFacts": [
            {
                "factId": "fact-1",
                "placeId": "place-1",
                "text": FACT_TEXT,
                "kind": "FACT",
                "evidenceIds": ["evidence-1"],
                "supportType": "CANONICAL_VALUE",
                "timeScope": "TIMELESS",
                "relation": None,
            }
        ],
    }


def test_fixed_contract_fixtures_validate_as_a_grounded_set() -> None:
    plan = ApprovedQueryPlan.model_validate(contract_payload("accepted-approved-hybrid"))
    evidence = EvidenceSet.model_validate(contract_payload("accepted-evidenceset"))
    proposal = ValidatedProposal.model_validate(contract_payload("accepted-validatedproposal"))

    validate_artifact(evidence, plan, current_versions=plan.versions)
    validate_artifact(proposal, plan, current_versions=plan.versions, evidence_set=evidence)
    assert_claims_bound_to_same_place(proposal, evidence)


def test_gemini_output_reproducing_fixed_fixture_passes_contract_validation() -> None:
    data = gemini_generation_input()
    gemini_output = {
        "places": [
            {
                "placeId": "place-1",
                "reasonClaims": [
                    {
                        "claimId": "claim-1",
                        "factId": "fact-1",
                        "text": FACT_TEXT,
                        "kind": "FACT",
                        "evidenceIds": ["evidence-1"],
                    }
                ],
            }
        ],
        "summaryClaims": [],
    }
    transport = FixedOutputTransport(gemini_output)
    adapter = GeminiAdapter(
        GeminiConfig("grounded-test", "gemini-test", 2048, GeminiPricing(0, 0)),
        transport,
        api_key="synthetic-key",
        telemetry_sink=InMemoryTelemetrySink(),
    )
    result = asyncio.run(
        EvidenceGenerator(adapter).generate(
            GenerationInput.model_validate(data),
            timeout_seconds=1,
        )
    )

    assert result.fallback is None
    assert len(transport.requests) == 1
    proposal = result.proposal
    assert proposal.generation_status == "GENERATED"
    assert proposal.candidate_place_ids == ("place-1",)
    evidence = EvidenceSet.model_validate(data["evidenceSet"])
    validate_artifact(
        proposal,
        ApprovedQueryPlan.model_validate(data["approvedPlan"]),
        current_versions=evidence.versions,
        evidence_set=evidence,
    )
    assert_claims_bound_to_same_place(proposal, evidence)


def test_gemini_claim_citing_other_place_evidence_is_rejected_before_publish() -> None:
    data = gemini_generation_input()
    evidence = data["evidenceSet"]
    evidence["evidence"].append(
        {
            **evidence["evidence"][0],
            "evidenceId": "evidence-2",
            "chunkId": "chunk-2",
            "placeId": "place-2",
        }
    )
    evidence["allowedPlaceIds"] = ["place-1", "place-2"]
    output = {
        "places": [
            {
                "placeId": "place-1",
                "reasonClaims": [
                    {
                        "claimId": "claim-1",
                        "factId": "fact-1",
                        "text": FACT_TEXT,
                        "kind": "FACT",
                        "evidenceIds": ["evidence-2"],
                    }
                ],
            }
        ],
        "summaryClaims": [],
    }
    adapter = GeminiAdapter(
        GeminiConfig("grounded-test", "gemini-test", 2048, GeminiPricing(0, 0)),
        FixedOutputTransport(output),
        api_key="synthetic-key",
        telemetry_sink=InMemoryTelemetrySink(),
    )
    result = asyncio.run(
        EvidenceGenerator(adapter).generate(GenerationInput.model_validate(data), timeout_seconds=1)
    )

    assert result.fallback is not None
    assert result.proposal.places == ()
    assert result.proposal.generation_status != "GENERATED"


@pytest.mark.parametrize("place_id", ["place-1", "place-with-dash"])
def test_lookup_built_proposal_binds_every_claim_to_its_own_place_evidence(place_id: str) -> None:
    plan = ApprovedQueryPlan.model_validate(contract_payload("accepted-approved-hybrid"))
    outcome = PlaceLookupOutcome(
        disposition=PlaceLookupDisposition.COMPLETE,
        places=(
            CanonicalPlaceProjection.model_validate(
                {
                    "placeId": place_id,
                    "publicAddress": "서울 종로구 자하문로5길 5",
                    "regionCode": "SEOUL",
                    "categoryCode": "HANOK",
                    "publicStatus": "PUBLIC",
                }
            ),
        ),
    )
    evidence, proposal = build_evidence_and_proposal_from_lookup(plan, outcome)

    validate_artifact(evidence, plan, current_versions=plan.versions)
    validate_artifact(proposal, plan, current_versions=plan.versions, evidence_set=evidence)
    assert_claims_bound_to_same_place(proposal, evidence)


def test_claim_pointing_at_evidence_of_another_place_is_a_contract_violation() -> None:
    plan = ApprovedQueryPlan.model_validate(contract_payload("accepted-approved-hybrid"))
    evidence = EvidenceSet.model_validate(contract_payload("accepted-evidenceset"))
    proposal_payload = contract_payload("accepted-validatedproposal")
    proposal_payload["places"][0]["placeId"] = "place-other"
    proposal_payload["candidatePlaceIds"] = ["place-other"]
    proposal = ValidatedProposal.model_validate(proposal_payload)

    with pytest.raises(ContractViolation):
        validate_artifact(proposal, plan, current_versions=plan.versions, evidence_set=evidence)
