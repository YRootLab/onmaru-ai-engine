"""Harness-style (Target / Dataset / Metrics / Threshold) and Microsoft Foundry-aligned
RAG Groundedness & Relevance evaluator.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class GroundednessCaseInput:
    case_id: str
    query: str
    expected_region_code: str | None
    candidate_refs: tuple[str, ...]
    ordered_refs: tuple[str, ...]
    relaxed_constraints: tuple[str, ...]
    stops: tuple[Mapping[str, str], ...]
    evidence_contexts: tuple[Mapping[str, str], ...]


@dataclass(frozen=True)
class GroundednessCaseScore:
    case_id: str
    safety_passed: bool
    stop_coverage: float
    region_consistency_passed: bool
    context_grounded_score: float
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class HarnessEvalThresholds:
    min_safety_rate: float = 1.0
    min_stop_coverage: float = 0.9
    min_region_consistency_rate: float = 0.9
    min_context_grounded_score: float = 0.8


@dataclass(frozen=True)
class HarnessEvalSummary:
    total_cases: int
    safety_rate: float
    mean_stop_coverage: float
    region_consistency_rate: float
    mean_context_grounded_score: float
    passed: bool
    case_scores: tuple[GroundednessCaseScore, ...]


def evaluate_groundedness_case(case: GroundednessCaseInput) -> GroundednessCaseScore:
    """Evaluates a single live RAG generation against its supplied evidenceContext."""
    reasons: list[str] = []
    allowed = set(case.candidate_refs)
    ordered_set = set(case.ordered_refs)

    # 1. Safety: never invent refs outside candidateRefs when candidateRefs are supplied
    safety_passed = (not allowed) or ordered_set.issubset(allowed)
    if not safety_passed:
        reasons.append("INVENTED_OR_OUT_OF_CANDIDATE_REF")

    # 2. Evidence coverage & text grounding against supplied evidenceContext
    ctx_by_place: dict[str, Mapping[str, str]] = {}
    for ctx in case.evidence_contexts:
        place_ref = str(ctx.get("placeRef") or "").strip()
        if place_ref:
            ctx_by_place[place_ref] = ctx

    stops_by_ref = {str(s.get("ref") or ""): str(s.get("reason") or "") for s in case.stops}

    covered_stops = 0
    grounded_hits = 0
    expected_stops = len(case.ordered_refs)
    for ref in case.ordered_refs:
        matched_ctx = ctx_by_place.get(ref)
        stop_reason = stops_by_ref.get(ref, "")
        if matched_ctx is not None:
            covered_stops += 1
            title = str(matched_ctx.get("title") or "").strip()
            # Grounded if reason cites real place title (or core tokens of title) or excerpt terms
            title_tokens = [tok for tok in title.split() if len(tok) >= 2]
            if (title and title in stop_reason) or any(tok in stop_reason for tok in title_tokens):
                grounded_hits += 1
            else:
                reasons.append(f"UNGROUNDED_REASON_FOR:{ref}")
        else:
            reasons.append(f"MISSING_EVIDENCE_CONTEXT:{ref}")

    stop_coverage = covered_stops / expected_stops if expected_stops else 1.0
    context_grounded_score = grounded_hits / expected_stops if expected_stops else 1.0

    # 3. Region consistency: if expected_region_code is set and ALL ordered stops belong to a
    #    different region in evidenceContext, relaxedConstraints must acknowledge "region".
    region_consistency_passed = True
    if case.expected_region_code and case.ordered_refs and ctx_by_place:
        expected_reg = case.expected_region_code.strip().upper()
        matched_regions = [
            str(ctx_by_place[ref].get("regionCode") or "").strip().upper()
            for ref in case.ordered_refs
            if ref in ctx_by_place and str(ctx_by_place[ref].get("regionCode") or "").strip()
        ]
        if (
            matched_regions
            and not any(r == expected_reg for r in matched_regions)
            and "region" not in {c.strip().lower() for c in case.relaxed_constraints}
        ):
            region_consistency_passed = False
            reasons.append("REGION_MISMATCH_WITHOUT_RELAXATION")

    return GroundednessCaseScore(
        case_id=case.case_id,
        safety_passed=safety_passed,
        stop_coverage=round(stop_coverage, 4),
        region_consistency_passed=region_consistency_passed,
        context_grounded_score=round(context_grounded_score, 4),
        reasons=tuple(reasons),
    )


def evaluate_groundedness_suite(
    cases: Sequence[GroundednessCaseInput],
    thresholds: HarnessEvalThresholds | None = None,
) -> HarnessEvalSummary:
    """Evaluates a dataset of live/captured RAG runs against Harness blocking thresholds."""
    if not cases:
        raise ValueError("cases must not be empty")
    active_thresholds = thresholds or HarnessEvalThresholds()
    scores = tuple(evaluate_groundedness_case(case) for case in cases)
    n = len(scores)

    safety_rate = sum(s.safety_passed for s in scores) / n
    mean_stop_coverage = sum(s.stop_coverage for s in scores) / n
    region_consistency_rate = sum(s.region_consistency_passed for s in scores) / n
    mean_context_grounded_score = sum(s.context_grounded_score for s in scores) / n

    passed = (
        safety_rate >= active_thresholds.min_safety_rate
        and mean_stop_coverage >= active_thresholds.min_stop_coverage
        and region_consistency_rate >= active_thresholds.min_region_consistency_rate
        and mean_context_grounded_score >= active_thresholds.min_context_grounded_score
    )
    return HarnessEvalSummary(
        total_cases=n,
        safety_rate=round(safety_rate, 4),
        mean_stop_coverage=round(mean_stop_coverage, 4),
        region_consistency_rate=round(region_consistency_rate, 4),
        mean_context_grounded_score=round(mean_context_grounded_score, 4),
        passed=passed,
        case_scores=scores,
    )
