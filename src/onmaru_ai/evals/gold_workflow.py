"""W22 Gold dataset curation workflow, quotas, leak detection, and sealing procedure."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from onmaru_ai.contracts.models import Route

ROUTES: tuple[Route, ...] = (
    "SQL_ONLY",
    "LEXICAL_ONLY",
    "DENSE_ONLY",
    "HYBRID",
    "SQL_PLUS_RETRIEVAL",
    "CLARIFY_OR_SCOPE",
)


class SplitLeakageError(Exception):
    """Raised when an entity appears across both development and sealed splits."""


@dataclass(frozen=True, slots=True)
class GoldDatasetQuota:
    dev_count: int = 200
    sealed_count: int = 100
    min_dev_per_route: int = 30
    min_sealed_per_route: int = 15

    @property
    def total_count(self) -> int:
        return self.dev_count + self.sealed_count


@dataclass(frozen=True, slots=True)
class SealedManifest:
    dataset_version: str
    dataset_hash: str
    sealed_by: str
    case_count: int
    is_sealed: bool = True


def validate_dataset_quotas(
    cases: Sequence[Mapping[str, Any]],
    quota: GoldDatasetQuota | None = None,
) -> None:
    q = quota or GoldDatasetQuota()
    dev_cases = [c for c in cases if c.get("split") == "development"]
    sealed_cases = [c for c in cases if c.get("split") == "sealed"]

    if len(dev_cases) < q.dev_count:
        raise ValueError(f"Insufficient development cases: {len(dev_cases)} < {q.dev_count}")
    if len(sealed_cases) < q.sealed_count:
        raise ValueError(f"Insufficient sealed cases: {len(sealed_cases)} < {q.sealed_count}")

    dev_route_counts = Counter(c.get("goldRoute") for c in dev_cases)
    sealed_route_counts = Counter(c.get("goldRoute") for c in sealed_cases)

    for route in ROUTES:
        if dev_route_counts[route] < q.min_dev_per_route:
            raise ValueError(
                f"Development quota for route {route} not met: "
                f"{dev_route_counts[route]} < {q.min_dev_per_route}"
            )
        if sealed_route_counts[route] < q.min_sealed_per_route:
            raise ValueError(
                f"Sealed quota for route {route} not met: "
                f"{sealed_route_counts[route]} < {q.min_sealed_per_route}"
            )


class GoldWorkflowManager:
    """Manages gold case validation, independent reviews, leakage checks, and sealing."""

    def validate_review_integrity(self, case: Mapping[str, Any]) -> None:
        reviews = case.get("reviews") or []
        reviewer_ids = {r.get("reviewerId") for r in reviews if isinstance(r, dict)}
        if len(reviewer_ids) != 2:
            raise ValueError("two distinct independent reviewers are required")

        adjudication = case.get("adjudication") or {}
        if not isinstance(adjudication, dict):
            raise ValueError("adjudication object required")
        if adjudication.get("decision") != "ACCEPT":
            raise ValueError("gold case requires ACCEPT adjudication")

    def check_split_leakage(
        self,
        dev_cases: Sequence[Mapping[str, Any]],
        sealed_cases: Sequence[Mapping[str, Any]],
    ) -> None:
        dev_places = {c["placeId"] for c in dev_cases if "placeId" in c}
        dev_sources = {
            (c["sourceId"], c["sourceRevision"])
            for c in dev_cases
            if "sourceId" in c and "sourceRevision" in c
        }

        for c in sealed_cases:
            pid = c.get("placeId")
            if pid and pid in dev_places:
                raise SplitLeakageError(f"Leakage detected for place:{pid}")
            sid = c.get("sourceId")
            srev = c.get("sourceRevision")
            if sid and srev and (sid, srev) in dev_sources:
                raise SplitLeakageError(f"Leakage detected for source:{sid}:{srev}")

    def seal_dataset(self, dataset: Mapping[str, Any], *, sealed_by: str) -> SealedManifest:
        serialized = json.dumps(dataset, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        d_hash = "sha256:" + hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        cases = dataset.get("cases") or []
        version = str(dataset.get("datasetVersion", "v1.0"))

        return SealedManifest(
            dataset_version=version,
            dataset_hash=d_hash,
            sealed_by=sealed_by,
            case_count=len(cases),
            is_sealed=True,
        )
