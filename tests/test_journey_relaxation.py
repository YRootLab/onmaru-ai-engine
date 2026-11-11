from __future__ import annotations

from onmaru_ai.journey_llm import RESPONSE_SCHEMA, JourneyLlmService
from onmaru_ai.security.internal_auth import JourneyProposalRequest, _proposal_response


def _body(candidate_refs: list[str]) -> JourneyProposalRequest:
    return JourneyProposalRequest.model_validate(
        {
            "schemaVersion": "internal.ai.v1",
            "requestId": "req-ai-001",
            "runId": "run-ai-001",
            "candidateCount": len(candidate_refs),
            "candidateRefs": candidate_refs,
        }
    )


def test_relaxed_constraints_are_passed_through_and_candidate_count_is_reported() -> None:
    response = _proposal_response(
        _body(["place:001", "place:002"]),
        {
            "orderedRefs": ["place:002"],
            "relaxedConstraints": ["THEME", "REGION"],
            "stops": [],
        },
        (),
    )

    assert response["outcome"] == "PROPOSAL"
    assert response["candidateCount"] == 2
    assert response["relaxedConstraints"] == ["THEME", "REGION"]
    assert "degradedReason" not in response


def test_missing_relaxed_constraints_defaults_to_empty_list() -> None:
    response = _proposal_response(
        _body(["place:001"]), {"orderedRefs": ["place:001"], "stops": []}, ()
    )

    assert response["relaxedConstraints"] == []


def test_no_result_with_candidates_reports_no_relevant_candidates() -> None:
    response = _proposal_response(
        _body(["place:001"]), {"orderedRefs": [], "relaxedConstraints": [], "stops": []}, ()
    )

    assert response["outcome"] == "NO_RESULTS"
    assert response["degradedReason"] == "NO_RELEVANT_CANDIDATES"


def test_no_result_without_candidates_reports_no_candidates() -> None:
    response = _proposal_response(_body([]), {"orderedRefs": [], "stops": []}, ())

    assert response["outcome"] == "NO_RESULTS"
    assert response["degradedReason"] == "NO_CANDIDATES"


def test_relaxed_constraints_is_optional_in_response_schema() -> None:
    assert "relaxedConstraints" in RESPONSE_SCHEMA["properties"]
    assert "relaxedConstraints" not in RESPONSE_SCHEMA["required"]


def test_filter_drops_relaxed_refs_outside_candidates() -> None:
    service = JourneyLlmService(adapter=None)  # type: ignore[arg-type]
    filtered = service._filter_proposal(
        {
            "orderedRefs": ["place:999", "place:001"],
            "stops": [],
            "relaxedConstraints": ["CATEGORY"],
        },
        ["place:001"],
    )

    assert filtered is not None
    assert filtered["orderedRefs"] == ["place:001"]
    assert filtered["relaxedConstraints"] == ["CATEGORY"]
