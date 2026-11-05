"""Hand-reviewed route golds: wrong route, dropped meaning or scope must fail."""
from __future__ import annotations

import importlib
import json
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

import pytest

from onmaru_ai.contracts import PlanProposal, SafeQueryRequest, validate_plan
from onmaru_ai.corpus.index import DeterministicEmbeddingProvider, EvidenceRetriever
from onmaru_ai.providers.gemini.adapter import GeminiAdapter


def request(query: str, **context: Any) -> SafeQueryRequest:
    return SafeQueryRequest.model_validate({
        "schemaVersion": "ai-safe-query.v1",
        "runId": "45e6a7f5-31bc-469d-9e30-6f510a1dc497",
        "safeQuery": query,
        "confirmedContext": {"regionCode": None, "pinnedPlaceIds": [],
                             "excludedPlaceIds": [], "lastConfirmedPlaceIds": [], **context},
        "authorityBounds": {
            "filters": {"filterHash": "sha256:" + "a" * 64, "publicOnly": True,
                        "placeIds": None, "regionCodes": None, "categoryCodes": None,
                        "pinnedPlaceIds": [], "excludedPlaceIds": []},
            "allowedCanonicalFields": ["PUBLIC_ADDRESS", "REGION_CODE", "CATEGORY_CODE",
                                       "PUBLIC_STATUS"]},
        "versions": {"corpusRevision": "corpus-1", "configHash": "sha256:" + "a" * 64,
                     "questionDictionaryVersion": "questions-1", "sourceRevocationSequence": 7},
        "limits": {"bm25K": 20, "vectorK": 20, "rerankK": 30, "evidenceK": 12, "maxPlaces": 5},
    })


def planner() -> Any:
    # Delayed import makes the initial RED a missing-feature assertion, not collection failure.
    assert importlib.util.find_spec("onmaru_ai.query") is not None, "W7 query planner is missing"
    from onmaru_ai.query import CatalogEntry, QueryPlanner

    return QueryPlanner(catalog=(
        CatalogEntry(code="JEONJU", kind="REGION", display_label="전주", synonyms=("전주시",)),
        CatalogEntry(code="SEOUL", kind="REGION", display_label="서울", synonyms=("서울시",)),
        CatalogEntry(code="BUSAN", kind="REGION", display_label="부산"),
        CatalogEntry(code="GYEONGGI", kind="REGION", display_label="경기"),
        CatalogEntry(code="p1", kind="PLACE", display_label="경복궁", region_code="SEOUL"),
        CatalogEntry(code="p2", kind="PLACE", display_label="덕수궁", region_code="SEOUL"),
        CatalogEntry(code="p3", kind="PLACE", display_label="전주한옥마을", region_code="JEONJU",
                     synonyms=("전주 한옥마을",)),
        CatalogEntry(code="p4", kind="PLACE", display_label="중앙시장", region_code="SEOUL"),
        CatalogEntry(code="p5", kind="PLACE", display_label="중앙시장", region_code="BUSAN"),
    ))


GOLDS = json.loads((Path(__file__).parent / "route-golds.json").read_text())


@pytest.mark.parametrize("gold", GOLDS, ids=[gold["name"] for gold in GOLDS])
def test_route_gold_preserves_meaning_and_scope(gold: dict[str, Any]) -> None:
    req = request(gold["query"], **gold.get("context", {}))
    plan = planner().plan(req)
    assert isinstance(plan, PlanProposal)
    validate_plan(req, plan)
    assert plan.route == gold["route"]
    assert plan.retrieval_mode == gold.get("mode", gold["route"])
    if "reason" in gold:
        assert plan.clarification is not None
        assert plan.clarification.reason == gold["reason"]
        assert plan.semantic_query is None
    else:
        assert plan.question_frame.operation == gold["operation"]
        assert list(plan.question_frame.target_place_ids) == gold.get("targets", [])
        assert set(plan.retrieval_expression.positive_concept_codes) == set(
            gold.get("positive", [])
        )
        assert set(plan.retrieval_expression.negative_concept_codes) == set(
            gold.get("negative", [])
        )
        assert list(plan.requested_canonical_fields) == gold.get("fields", [])
        if "regions" in gold:
            assert list(plan.proposed_filters.region_codes or ()) == gold["regions"]
        if "pins" in gold:
            assert list(plan.proposed_filters.pinned_place_ids) == gold["pins"]
        if "excludes" in gold:
            assert list(plan.proposed_filters.excluded_place_ids) == gold["excludes"]
        if plan.retrieval_mode != "NONE":
            # Original negation/modifiers/order survive; no code-label replacement.
            assert plan.semantic_query == gold["query"]


def test_normalization_preserves_quotes_numbers_and_negation() -> None:
    module = planner()
    req = request(unicodedata.normalize("NFD", '  전주에서\t“한옥”  3곳\n시장 말고 '))
    result = module.plan(req)
    assert result.route == "HYBRID"
    assert result.semantic_query == '전주에서 "한옥" 3곳 시장 말고'
    assert result.retrieval_expression.negative_concept_codes == ("TRADITIONAL_MARKET",)


@pytest.mark.parametrize("gold", GOLDS, ids=[gold["name"] for gold in GOLDS])
def test_planning_never_dispatches_providers(gold: dict[str, Any], monkeypatch: pytest.MonkeyPatch
                                           ) -> None:
    calls: Counter[str] = Counter()

    def forbidden(name: str) -> Any:
        def dispatch(*args: Any, **kwargs: Any) -> Any:
            calls[name] += 1
            raise AssertionError("planning must not dispatch " + name)
        return dispatch

    monkeypatch.setattr(DeterministicEmbeddingProvider, "embed", forbidden("embedding"))
    monkeypatch.setattr(EvidenceRetriever, "retrieve", forbidden("retrieval"))
    monkeypatch.setattr(GeminiAdapter, "generate", forbidden("llm"))
    monkeypatch.setattr(GeminiAdapter, "stream", forbidden("llm"))
    plan = planner().plan(request(gold["query"], **gold.get("context", {})))
    assert plan.route == gold["route"]
    assert calls == Counter()


def test_deterministic_hash_and_version_echo() -> None:
    req = request("전주에서 조용한 한옥 3곳")
    first = planner().plan(req)
    second = planner().plan(req)
    assert first == second
    assert first.versions == req.versions
    assert first.limits == req.limits
    assert first.proposed_filters.filter_hash == req.authority_bounds.filters.filter_hash


@pytest.mark.parametrize("field,value", [
    ("placeIds", []), ("placeIds", ["p2"]), ("regionCodes", ["BUSAN"]),
    ("excludedPlaceIds", ["p1"]),
])
def test_explicit_targets_cannot_expand_authority(field: str, value: list[str]) -> None:
    payload = request("서울 경복궁 주소").model_dump(mode="json", by_alias=True)
    payload["authorityBounds"]["filters"][field] = value
    req = SafeQueryRequest.model_validate(payload)
    plan = planner().plan(req)
    assert plan.route == "CLARIFY_OR_SCOPE"
    validate_plan(req, plan)


def test_dictionary_mismatch_is_closed_contract_failure() -> None:
    from onmaru_ai.contracts import ContractViolation
    payload = request("경복궁 주소").model_dump(mode="json", by_alias=True)
    payload["versions"]["questionDictionaryVersion"] = "questions-unknown"
    with pytest.raises(ContractViolation, match="VERSION_MISMATCH"):
        planner().plan(SafeQueryRequest.model_validate(payload))
