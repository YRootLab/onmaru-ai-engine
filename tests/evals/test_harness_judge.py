from __future__ import annotations

from onmaru_ai.evals.harness_judge import (
    GroundednessCaseInput,
    HarnessEvalThresholds,
    evaluate_groundedness_case,
    evaluate_groundedness_suite,
)


def test_harness_judge_passes_grounded_case() -> None:
    case = GroundednessCaseInput(
        case_id="case-ok",
        query="경주 역사 여행",
        expected_region_code="KR-47",
        candidate_refs=("p-tourapi-1", "p-tourapi-2"),
        ordered_refs=("p-tourapi-1",),
        relaxed_constraints=(),
        stops=(
            {
                "ref": "p-tourapi-1",
                "reason": "불국사는 경주의 대표적인 유네스코 세계유산 사찰입니다.",
            },
        ),
        evidence_contexts=(
            {
                "evidenceRef": "rev-1:chunk:c1",
                "placeRef": "p-tourapi-1",
                "title": "불국사",
                "regionCode": "KR-47",
                "categoryCode": "HISTORIC_SITE",
                "excerpt": "경상북도 경주시에 위치한 신라 시대의 사찰",
            },
        ),
    )
    score = evaluate_groundedness_case(case)
    assert score.safety_passed is True
    assert score.stop_coverage == 1.0
    assert score.region_consistency_passed is True
    assert score.context_grounded_score == 1.0
    assert score.reasons == ()


def test_harness_judge_catches_invented_ref_and_region_mismatch() -> None:
    bad_safety = GroundednessCaseInput(
        case_id="case-bad-ref",
        query="경주 여행",
        expected_region_code="KR-47",
        candidate_refs=("p-tourapi-1",),
        ordered_refs=("p-tourapi-999",),
        relaxed_constraints=(),
        stops=({"ref": "p-tourapi-999", "reason": "임의 생성 장소"},),
        evidence_contexts=(),
    )
    bad_score = evaluate_groundedness_case(bad_safety)
    assert bad_score.safety_passed is False
    assert "INVENTED_OR_OUT_OF_CANDIDATE_REF" in bad_score.reasons

    region_mismatch = GroundednessCaseInput(
        case_id="case-region-unrelaxed",
        query="제주 바다 여행",
        expected_region_code="KR-50",
        candidate_refs=("p-tourapi-10",),
        ordered_refs=("p-tourapi-10",),
        relaxed_constraints=(),
        stops=({"ref": "p-tourapi-10", "reason": "경복궁 산책"},),
        evidence_contexts=(
            {
                "placeRef": "p-tourapi-10",
                "title": "경복궁",
                "regionCode": "KR-11",
            },
        ),
    )
    mismatch_score = evaluate_groundedness_case(region_mismatch)
    assert mismatch_score.region_consistency_passed is False
    assert "REGION_MISMATCH_WITHOUT_RELAXATION" in mismatch_score.reasons

    region_relaxed = GroundednessCaseInput(
        case_id="case-region-relaxed",
        query="제주 바다 여행",
        expected_region_code="KR-50",
        candidate_refs=("p-tourapi-10",),
        ordered_refs=("p-tourapi-10",),
        relaxed_constraints=("region",),
        stops=({"ref": "p-tourapi-10", "reason": "경복궁 산책으로 지역 조건을 완화했습니다."},),
        evidence_contexts=(
            {
                "placeRef": "p-tourapi-10",
                "title": "경복궁",
                "regionCode": "KR-11",
            },
        ),
    )
    relaxed_score = evaluate_groundedness_case(region_relaxed)
    assert relaxed_score.region_consistency_passed is True

    summary = evaluate_groundedness_suite(
        [bad_safety, region_relaxed],
        HarnessEvalThresholds(),
    )
    assert summary.total_cases == 2
    assert summary.passed is False
    assert summary.safety_rate == 0.5
