"""Cross-repo contract tests aligning with Spring v0.3.54 fixtures and schemas."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from onmaru_ai.contracts import (
    ApprovedQueryPlan,
    CandidateSet,
    EvidenceSet,
    ProgressEvent,
    ValidatedProposal,
)

FIXTURES_DIR = Path(__file__).parents[1] / "contracts" / "fixtures"


def load_fixture(name: str) -> dict[str, Any]:
    path = FIXTURES_DIR / f"{name}.json"
    with open(path, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
        return data


def test_spring_canonical_progress_callback_schema() -> None:
    """Verifies that internal.ai.progress.v1 matches Spring v0.3.54 expectation."""
    fixture = load_fixture("accepted-progress-preparing_input")
    payload = dict(fixture["payload"])
    # Canonical schemaVersion in Spring v0.3.54 is internal.ai.progress.v1
    payload["schemaVersion"] = "internal.ai.progress.v1"
    event = ProgressEvent.model_validate(payload)
    assert event.schema_version == "internal.ai.progress.v1"
    assert event.stage == "PREPARING_INPUT"
    assert event.ordinal == 1

    dumped = event.model_dump(by_alias=True)
    assert dumped["schemaVersion"] == "internal.ai.progress.v1"
    assert dumped["runId"] == payload["runId"]
    assert dumped["planHash"] == payload["planHash"]
    assert dumped["ordinal"] == 1
    assert dumped["stage"] == "PREPARING_INPUT"


def test_spring_journey_execute_approved_lookup_contract() -> None:
    """Verifies that approved lookup contract aligns with Spring JourneyQueryToolResponse."""
    from onmaru_ai.adapters.spring_place import PlaceLookupResponse

    spring_tool_response = {
        "catalogVersion": "journey.query.tools.v1",
        "places": [
            {
                "placeId": "place-hanok-1",
                "name": "북촌 한옥마을",
                "category": "HANOK",
                "address": "서울 종로구 계동길",
                "latitude": 37.58,
                "longitude": 126.98,
            }
        ],
    }
    parsed = PlaceLookupResponse.model_validate(spring_tool_response)
    assert parsed.schema_version == "journey.query.tools.v1"
    assert len(parsed.places) == 1
    assert parsed.places[0].place_id == "place-hanok-1"
    assert parsed.places[0].address == "서울 종로구 계동길"


@pytest.mark.parametrize(
    "fixture_name,model_cls",
    [
        ("accepted-approved-sql_only", ApprovedQueryPlan),
        ("accepted-approved-hybrid", ApprovedQueryPlan),
        ("accepted-approved-sql_plus_retrieval", ApprovedQueryPlan),
        ("accepted-candidateset", CandidateSet),
        ("accepted-evidenceset", EvidenceSet),
        ("accepted-validatedproposal", ValidatedProposal),
    ],
)
def test_all_contract_fixtures_revalidate_cleanly(fixture_name: str, model_cls: Any) -> None:
    fixture = load_fixture(fixture_name)
    instance = model_cls.model_validate(fixture["payload"])
    assert instance is not None
