"""Deterministic W17 replay metrics over reviewed W16 gold datasets."""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from onmaru_ai.contracts.models import Route

Stage = Literal["BM25", "VECTOR", "RRF", "RERANK", "EVIDENCE"]
STAGES: tuple[Stage, ...] = ("BM25", "VECTOR", "RRF", "RERANK", "EVIDENCE")
Identifier = Annotated[str, Field(min_length=1, max_length=128)]


class ReplayModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ClaimResult(ReplayModel):
    claim_id: Identifier = Field(alias="claimId")
    decision: Literal["SUPPORTED", "HELD"]


class ReplayRun(ReplayModel):
    query_id: Identifier = Field(alias="queryId")
    actual_route: Route = Field(alias="actualRoute")
    stages: dict[Stage, tuple[Identifier, ...]]
    selected_place_ids: tuple[Identifier, ...] = Field(alias="selectedPlaceIds")
    claims: tuple[ClaimResult, ...]
    violation_codes: tuple[
        Literal["HARD_FILTER", "RIGHTS", "REVOCATION", "SOURCE_SCOPE"], ...
    ] = Field(default=(), alias="violationCodes")

    @model_validator(mode="after")
    def complete_stages(self) -> ReplayRun:
        if set(self.stages) != set(STAGES):
            raise ValueError("each run must provide every replay stage")
        if any(len(refs) != len(set(refs)) for refs in self.stages.values()):
            raise ValueError("stage results must be unique")
        if len({claim.claim_id for claim in self.claims}) != len(self.claims):
            raise ValueError("claim results must be unique")
        return self


class ReplayInput(ReplayModel):
    schema_version: Literal["rag-replay.v1"] = Field(alias="schemaVersion")
    corpus_revision: Identifier = Field(alias="corpusRevision")
    config_hash: str = Field(alias="configHash", pattern=r"^sha256:[a-f0-9]{64}$")
    dataset: dict[str, object]
    runs: tuple[ReplayRun, ...]


class Ratio(ReplayModel):
    numerator: int = Field(ge=0)
    denominator: int = Field(ge=0)
    value: float = Field(ge=0, le=1)


class StageMetrics(ReplayModel):
    stage: Stage
    recall_at_k: Ratio = Field(alias="recallAtK")
    mrr: Ratio
    ndcg_at_k: Ratio = Field(alias="ndcgAtK")


class ClaimMetrics(ReplayModel):
    supported: int = Field(ge=0)
    held: int = Field(ge=0)


class RagReplayReport(ReplayModel):
    schema_version: Literal["rag-replay-report.v1"] = Field(alias="schemaVersion")
    corpus_revision: Identifier = Field(alias="corpusRevision")
    config_hash: str = Field(alias="configHash")
    dataset_hash: str = Field(alias="datasetHash")
    stages: tuple[StageMetrics, ...]
    route_confusion: dict[str, int] = Field(alias="routeConfusion")
    first_gold_loss: dict[Stage, int] = Field(alias="firstGoldLoss")
    place_recall_at_5: Ratio = Field(alias="placeRecallAt5")
    place_ndcg_at_5: Ratio = Field(alias="placeNdcgAt5")
    claims: ClaimMetrics
    hard_violations: int = Field(alias="hardViolations", ge=0)
    gates: dict[Literal["quality", "safety", "route"], bool]
    overall_passed: bool = Field(alias="overallPassed")
    promotion_eligible: bool = Field(alias="promotionEligible")
    report_hash: str = Field(alias="reportHash", pattern=r"^sha256:[a-f0-9]{64}$")


def evaluate_rag_replay(value: object) -> RagReplayReport:
    data = ReplayInput.model_validate(value)
    dataset = data.dataset
    cases = dataset.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("gold dataset has no cases")
    case_by_id = {case.get("queryId"): case for case in cases if isinstance(case, dict)}
    run_by_id = {run.query_id: run for run in data.runs}
    if len(run_by_id) != len(data.runs) or set(run_by_id) != set(case_by_id):
        raise ValueError("runs must match gold cases exactly once")
    if {case.get("corpusRevision") for case in cases} != {data.corpus_revision}:
        raise ValueError("corpus revision mismatch")

    stage_values: list[StageMetrics] = []
    first_loss: Counter[Stage] = Counter()
    confusion: Counter[str] = Counter()
    supported = held = hard_violations = 0
    place_recall_num = place_recall_den = 0
    place_ndcg_sum = 0.0
    place_measured = 0
    route_correct = 0

    for stage in STAGES:
        recall_num = recall_den = measured = 0
        reciprocal_sum = ndcg_sum = 0.0
        for query_id, case in case_by_id.items():
            run = run_by_id[str(query_id)]
            relevant = {
                item["chunkId"]: int(item["grade"])
                for item in case.get("goldEvidence", [])
                if int(item["grade"]) > 0
            }
            if not relevant:
                continue
            measured += 1
            results = run.stages[stage]
            recall_num += sum(ref in results for ref in relevant)
            recall_den += len(relevant)
            first_rank = next((i for i, ref in enumerate(results, 1) if ref in relevant), None)
            reciprocal_sum += 0 if first_rank is None else 1 / first_rank
            ndcg_sum += _ndcg(results, relevant)
        stage_values.append(
            StageMetrics(
                stage=stage,
                recallAtK=_ratio(recall_num, recall_den),
                mrr=_average_ratio(reciprocal_sum, measured),
                ndcgAtK=_average_ratio(ndcg_sum, measured),
            )
        )

    for query_id, case in case_by_id.items():
        run = run_by_id[str(query_id)]
        gold_route = str(case["goldRoute"])
        confusion[f"{gold_route}->{run.actual_route}"] += 1
        route_correct += run.actual_route == gold_route
        gold_chunks = {
            item["chunkId"] for item in case.get("goldEvidence", []) if int(item["grade"]) > 0
        }
        place_grades = {
            item["placeId"]: int(item["grade"])
            for item in case.get("placeGrades", [])
            if int(item["grade"]) > 0
        }
        if bool(case.get("answerable")) and place_grades:
            place_measured += 1
            place_recall_num += sum(
                place in run.selected_place_ids[:5] for place in place_grades
            )
            place_recall_den += len(place_grades)
            place_ndcg_sum += _ndcg(run.selected_place_ids[:5], place_grades)
        for stage in STAGES:
            if gold_chunks and not gold_chunks.intersection(run.stages[stage]):
                first_loss[stage] += 1
                break
        gold_claims = {item["claimId"] for item in case.get("minimumClaims", [])}
        supported_claims = {
            claim.claim_id
            for claim in run.claims
            if claim.decision == "SUPPORTED" and claim.claim_id in gold_claims
        }
        supported += len(supported_claims)
        held += len(gold_claims - supported_claims)
        hard_violations += sum(
            claim.decision == "SUPPORTED" and claim.claim_id not in gold_claims
            for claim in run.claims
        )
        allowed = set(case.get("allowedPlaceIds", []))
        forbidden = set(case.get("forbiddenPlaceIds", []))
        hard_violations += len(run.violation_codes)
        hard_violations += sum(
            place not in allowed or place in forbidden for place in run.selected_place_ids
        )

    evidence = stage_values[-1]
    place_recall = _ratio(place_recall_num, place_recall_den)
    place_ndcg = _average_ratio(place_ndcg_sum, place_measured)
    quality = (
        evidence.recall_at_k.value >= 0.90
        and place_recall.value >= 0.85
        and place_ndcg.value >= 0.75
    )
    route = route_correct == len(cases)
    safety = hard_violations == 0
    gates = {"quality": quality, "safety": safety, "route": route}
    overall = all(gates.values())
    sealed = all(case.get("split") == "sealed" for case in cases)
    base = {
        "schemaVersion": "rag-replay-report.v1",
        "corpusRevision": data.corpus_revision,
        "configHash": data.config_hash,
        "datasetHash": _hash(dataset),
        "stages": [item.model_dump(mode="json", by_alias=True) for item in stage_values],
        "routeConfusion": dict(sorted(confusion.items())),
        "firstGoldLoss": dict(sorted(first_loss.items())),
        "placeRecallAt5": place_recall.model_dump(mode="json", by_alias=True),
        "placeNdcgAt5": place_ndcg.model_dump(mode="json", by_alias=True),
        "claims": {"supported": supported, "held": held},
        "hardViolations": hard_violations,
        "gates": gates,
        "overallPassed": overall,
        "promotionEligible": overall and sealed,
    }
    return RagReplayReport.model_validate({**base, "reportHash": _hash(base)})


def _ratio(numerator: int, denominator: int) -> Ratio:
    return Ratio(
        numerator=numerator,
        denominator=denominator,
        value=round(numerator / denominator, 8) if denominator else 1.0,
    )


def _average_ratio(total: float, count: int) -> Ratio:
    scale = 100_000_000
    return Ratio(
        numerator=round(total * scale),
        denominator=count * scale,
        value=round(total / count, 8) if count else 1.0,
    )


def _ndcg(results: tuple[str, ...], grades: dict[str, int]) -> float:
    actual = math.fsum(
        (2 ** grades.get(ref, 0) - 1) / math.log2(rank + 1)
        for rank, ref in enumerate(results, 1)
    )
    ideal = math.fsum(
        (2**grade - 1) / math.log2(rank + 1)
        for rank, grade in enumerate(sorted(grades.values(), reverse=True), 1)
    )
    return actual / ideal if ideal else 1.0


def _hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(payload.encode()).hexdigest()
