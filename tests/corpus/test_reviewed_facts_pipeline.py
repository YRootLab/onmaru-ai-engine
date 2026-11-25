"""Tests for reviewed facts pipeline, data expansion, and fallback semantics (Issue #93)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from onmaru_ai.corpus.reviewed_facts import (
    ReviewedFactImport,
    parse_reviewed_facts_jsonl,
)
from onmaru_ai.generation.models import GenerationFallback, GenerationInput
from onmaru_ai.generation.service import EvidenceGenerator
from onmaru_ai.observability import InMemoryTelemetrySink
from onmaru_ai.providers.gemini.adapter import GeminiAdapter
from onmaru_ai.providers.gemini.models import (
    GeminiConfig,
    GeminiPricing,
    GeminiTransportRequest,
    GeminiTransportResponse,
)


def test_cultural_landmarks_approved_jsonl_parses_completely() -> None:
    path = (
        Path(__file__).parent.parent.parent
        / "artifacts"
        / "fact-review"
        / "cultural_landmarks.approved.jsonl"
    )
    assert path.is_file(), f"File {path} must exist"
    content = path.read_text(encoding="utf-8")
    facts = parse_reviewed_facts_jsonl(content)

    assert len(facts) == 10
    assert all(isinstance(f, ReviewedFactImport) for f in facts)
    assert all(f.review_status == "APPROVED" for f in facts)
    assert all(f.approved_by == "user-yangseunghyeon" for f in facts)

    # Unique fact IDs and place IDs
    fact_ids = [f.fact_id for f in facts]
    place_ids = [f.place_id for f in facts]
    assert len(set(fact_ids)) == 10
    assert len(set(place_ids)) == 10


def test_reviewed_fact_rejects_unapproved_status() -> None:
    bad_line = (
        '{"revisionId": "rev-1", "factId": "f-1", '
        '"chunkId": "2fa50b89-13d8-51ba-80f3-18b36936a168", '
        '"placeId": "p-1", "startOffset": 0, "endOffset": 10, '
        '"factText": "테스트 사실입니다.", '
        '"kind": "FACT", "supportType": "HISTORICAL_FACT", '
        '"timeScope": "2026", "relation": null, '
        '"reviewStatus": "PENDING", "approvedBy": "reviewer", '
        '"approvedAt": "2026-11-25T00:00:00+00:00"}'
    )
    with pytest.raises(ValueError):
        parse_reviewed_facts_jsonl(bad_line)


def test_reviewed_fact_rejects_multisentence_or_unsafe_text() -> None:
    multisentence = (
        '{"revisionId": "rev-1", "factId": "f-2", '
        '"chunkId": "2fa50b89-13d8-51ba-80f3-18b36936a168", '
        '"placeId": "p-1", "startOffset": 0, "endOffset": 20, '
        '"factText": "첫 문장입니다. 두 번째 문장입니다.", '
        '"kind": "FACT", "supportType": "HISTORICAL_FACT", '
        '"timeScope": "2026", "relation": null, '
        '"reviewStatus": "APPROVED", "approvedBy": "reviewer", '
        '"approvedAt": "2026-11-25T00:00:00+00:00"}'
    )
    with pytest.raises(ValueError):
        parse_reviewed_facts_jsonl(multisentence)


class FakeTransport:
    async def generate(self, _req: GeminiTransportRequest) -> GeminiTransportResponse:
        return GeminiTransportResponse(
            200, {"candidates": [{"content": {"parts": [{"text": "{}"}]}}]}
        )


@pytest.mark.anyio
async def test_evidence_generator_falls_back_when_place_has_no_verified_facts() -> None:
    """Validate that when verified_facts is empty, EvidenceGenerator emits NO_SUPPORTED_FACTS."""
    fixture_path = Path(__file__).parent.parent / "generation" / "fixtures" / "input.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    # Clear verified_facts to simulate places without human-approved facts
    data["verifiedFacts"] = []

    gen_input = GenerationInput.model_validate(data)
    adapter = GeminiAdapter(
        GeminiConfig("test", "test", 2048, GeminiPricing(0, 0)),
        FakeTransport(),  # type: ignore[arg-type]
        api_key="synthetic-key",
        telemetry_sink=InMemoryTelemetrySink(),
    )
    generator = EvidenceGenerator(adapter)

    result = await generator.generate(gen_input, timeout_seconds=1)

    assert result.fallback == GenerationFallback.NO_SUPPORTED_FACTS
    assert result.proposal.generation_status == "NOT_RUN"
    assert len(result.proposal.places) == 0
