"""Portable W0 contracts: failures here describe unsafe boundary changes."""

from __future__ import annotations

import json
from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import Any

import pytest
from jsonschema import Draft202012Validator
from pydantic import ValidationError

from onmaru_ai import contracts as api

ROOT = Path(__file__).parent
SCHEMAS = Path(api.__file__).parent / "schemas"


def fixture_cases() -> list[dict[str, Any]]:
    directory = ROOT / "fixtures"
    return [json.loads(path.read_text()) for path in sorted(directory.glob("*.json"))]


def test_seven_versioned_contracts_are_available() -> None:
    assert set(api.CONTRACT_MODELS) == {
        "SafeQueryRequest",
        "PlanProposal",
        "ApprovedQueryPlan",
        "CandidateSet",
        "EvidenceSet",
        "ValidatedProposal",
        "ProgressEvent",
    }


def test_shared_fixtures_cover_routes_and_rejection_boundaries() -> None:
    cases = fixture_cases()
    assert cases, "W0 must ship portable fixtures"
    accepted = [case for case in cases if case["expected"] == "ACCEPT"]
    assert {case["model"] for case in accepted} == {
        "SafeQueryRequest",
        "PlanProposal",
        "ApprovedQueryPlan",
        "CandidateSet",
        "EvidenceSet",
        "ValidatedProposal",
        "ProgressEvent",
    }
    assert {c["payload"]["route"] for c in accepted if c["model"] == "PlanProposal"} == {
        "SQL_ONLY",
        "LEXICAL_ONLY",
        "DENSE_ONLY",
        "HYBRID",
        "SQL_PLUS_RETRIEVAL",
        "CLARIFY_OR_SCOPE",
    }
    assert {
        "VERSION_MISMATCH",
        "FILTER_EXPANSION",
        "FILTER_MISMATCH",
        "PLAN_HASH_MISMATCH",
        "SOURCE_REVOKED",
        "UNEXPECTED_FIELD",
    } <= {c["expected"] for c in cases}


def test_checked_in_schemas_match_models_and_validate_every_fixture() -> None:
    for name, model in api.CONTRACT_MODELS.items():
        schema = json.loads((SCHEMAS / f"{name}.schema.json").read_text())
        assert schema == model.model_json_schema(by_alias=True)
        Draft202012Validator.check_schema(schema)
        validator = Draft202012Validator(schema)
        for case in fixture_cases():
            if case["model"] != name:
                continue
            errors = list(validator.iter_errors(case["payload"]))
            assert bool(errors) is not case["schemaValid"], case["name"]


@pytest.mark.parametrize("case", fixture_cases(), ids=lambda case: case["name"])
def test_portable_fixtures_have_the_declared_model_and_authority_result(
    case: dict[str, Any],
) -> None:
    model = api.CONTRACT_MODELS[case["model"]]
    if not case["schemaValid"] or case["expected"] == "INVALID_PAYLOAD":
        with pytest.raises(ValidationError):
            model.model_validate(case["payload"])
        return
    payload = model.model_validate(case["payload"])
    context = case.get("context")
    if context is None:
        assert case["expected"] == "ACCEPT"
        return
    request = api.SafeQueryRequest.model_validate(context["request"])
    proposal = api.PlanProposal.model_validate(context["proposal"])
    approved = api.ApprovedQueryPlan.model_validate(context["approved"])
    versions = api.Versions.model_validate(context["currentVersions"])
    revoked = tuple(api.SourceRevision.model_validate(item) for item in context["revokedSources"])
    action: Callable[[], None]
    if isinstance(payload, api.PlanProposal):
        action = partial(api.validate_plan, request, payload, current_versions=versions)
    elif isinstance(payload, api.ApprovedQueryPlan):
        action = partial(
            api.validate_approval,
            request,
            proposal,
            payload,
            current_versions=versions,
        )
    else:
        assert isinstance(
            payload, (api.CandidateSet, api.EvidenceSet, api.ValidatedProposal, api.ProgressEvent)
        )
        evidence = api.EvidenceSet.model_validate(context["evidence"])
        action = partial(
            api.validate_artifact,
            payload,
            approved,
            current_versions=versions,
            revoked_sources=revoked,
            evidence_set=evidence,
        )
    if case["expected"] == "ACCEPT":
        action()
    else:
        with pytest.raises(api.ContractViolation) as error:
            action()
        assert error.value.code == case["expected"], case["name"]


@pytest.mark.parametrize(
    "field",
    [
        "memberId",
        "member",
        "rawQuestion",
        "question",
        "conversation",
        "messages",
        "modelTokens",
        "tokens",
        "prompt",
        "sourceBody",
        "reasoning",
    ],
)
def test_sensitive_unknown_fields_are_rejected_at_every_contract_boundary(field: str) -> None:
    for case in fixture_cases():
        if case["expected"] != "ACCEPT":
            continue
        document = {**case["payload"], field: "forbidden"}
        with pytest.raises(ValidationError):
            api.CONTRACT_MODELS[case["model"]].model_validate(document)
        schema = api.CONTRACT_MODELS[case["model"]].model_json_schema(by_alias=True)
        assert not Draft202012Validator(schema).is_valid(document)


def object_paths(value: Any, path: tuple[str | int, ...] = ()) -> list[tuple[str | int, ...]]:
    """Find real fixture objects, including objects inside arrays."""
    paths = [path] if isinstance(value, dict) else []
    if isinstance(value, dict):
        for key, child in value.items():
            paths.extend(object_paths(child, (*path, key)))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            paths.extend(object_paths(child, (*path, index)))
    return paths


def test_nested_contract_objects_reject_sensitive_extras() -> None:
    for case in fixture_cases():
        if case["expected"] != "ACCEPT":
            continue
        for path in object_paths(case["payload"]):
            document = json.loads(json.dumps(case["payload"]))
            node = document
            for component in path:
                node = node[component]
            node["reasoning"] = "forbidden"
            with pytest.raises(ValidationError):
                api.CONTRACT_MODELS[case["model"]].model_validate(document)
            schema = api.CONTRACT_MODELS[case["model"]].model_json_schema(by_alias=True)
            assert not Draft202012Validator(schema).is_valid(document)


@pytest.mark.parametrize(
    "concept",
    [
        "HISTORY",
        "HISTORICAL_SIGNIFICANCE",
        "ARCHITECTURE",
        "CULTURAL_PRACTICE",
        "VISIT_POINT",
        "FAMILY_SUITABILITY",
        "QUIETNESS",
        "ACCESSIBILITY",
        "INDEPENDENCE_MOVEMENT",
        "JOSEON_PERIOD",
        "TRADITIONAL_MARKET",
        "HANOK",
        "K_CONTENT",
        "SOLO",
        "COUPLE",
        "FAMILY",
        "FRIENDS",
        "QUIET",
        "LIVELY",
        "WALKABLE",
    ],
)
def test_initial_dictionary_accepts_each_documented_search_concept(concept: str) -> None:
    case = json.loads((ROOT / "fixtures" / "accepted-plan-hybrid.json").read_text())
    payload = case["payload"]
    payload["questionFrame"]["subjectConceptCodes"] = [concept]
    payload["retrievalExpression"]["positiveConceptCodes"] = [concept]
    schema = api.PlanProposal.model_json_schema(by_alias=True)
    Draft202012Validator(schema).validate(payload)
    plan = api.PlanProposal.model_validate(payload)
    # This test isolates dictionary acceptance; fixed fixture literals separately test hashing.
    plan = plan.model_copy(update={"plan_hash": api.compute_plan_hash(plan)})
    api.validate_plan(api.SafeQueryRequest.model_validate(case["context"]["request"]), plan)


@pytest.mark.parametrize(
    "reason",
    [
        "CANONICAL_FACT_ONLY",
        "EXACT_PUBLIC_TERM",
        "SINGLE_SEMANTIC_TOPIC",
        "COMPOSITE_QUERY",
        "CANONICAL_FACT_WITH_RETRIEVAL",
        "AMBIGUOUS_TARGET",
        "CONFLICTING_CONDITIONS",
        "UNSUPPORTED_SCOPE",
        "SEMANTIC_LOSS",
    ],
)
def test_fixed_plan_reason_codes_are_serializable(reason: str) -> None:
    case = json.loads((ROOT / "fixtures" / "accepted-plan-hybrid.json").read_text())
    case["payload"]["reasonCodes"] = [reason]
    Draft202012Validator(api.PlanProposal.model_json_schema(by_alias=True)).validate(
        case["payload"]
    )
    plan = api.PlanProposal.model_validate(case["payload"])
    assert plan.model_dump(mode="json", by_alias=True)["reasonCodes"] == [reason]


@pytest.mark.parametrize(
    ("reason", "question_code"),
    [
        ("AMBIGUOUS_TARGET", "CHOOSE_TARGET"),
        ("CONFLICTING_CONDITIONS", "RESOLVE_CONDITIONS"),
        ("UNSUPPORTED_SCOPE", "SUPPORTED_TRAVEL_SCOPE"),
        ("SEMANTIC_LOSS", "PRESERVE_MEANING"),
    ],
)
def test_fixed_clarification_question_codes_are_serializable(
    reason: str, question_code: str
) -> None:
    case = json.loads((ROOT / "fixtures" / "accepted-plan-clarify_or_scope.json").read_text())
    case["payload"]["clarification"] = {"reason": reason, "questionCode": question_code}
    Draft202012Validator(api.PlanProposal.model_json_schema(by_alias=True)).validate(
        case["payload"]
    )
    plan = api.PlanProposal.model_validate(case["payload"])
    assert (
        plan.model_dump(mode="json", by_alias=True)["clarification"]["questionCode"]
        == question_code
    )
