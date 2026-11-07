"""Conservative support: exact reviewed assertions, never substring or model judging."""

from __future__ import annotations

import html
import re
import unicodedata

from onmaru_ai.contracts import validate_artifact
from onmaru_ai.contracts.models import Claim, PlaceClaims
from onmaru_ai.proposal.text_safety import is_safe_proposal_text

from .models import GenerationInput, ModelProposal, ProposedClaim, VerifiedFact


def validate_evidence(data: GenerationInput) -> None:
    validate_artifact(
        data.evidence_set,
        data.approved_plan,
        current_versions=data.current_versions,
        revoked_sources=data.revoked_sources,
    )
    evidence = {item.evidence_id: item for item in data.evidence_set.evidence}
    documents = {(item.source_id, item.source_revision): item for item in data.documents}
    if len(documents) != len(data.documents):
        raise ValueError("duplicate source document")
    spans: dict[str, str] = {}
    for ref, item in evidence.items():
        document = documents.get((item.source_id, item.source_revision))
        if (
            document is None
            or document.corpus_revision != data.current_versions.corpus_revision
            or item.end_offset > len(document.text)
            or item.end_offset - item.start_offset > 2000
        ):
            raise ValueError("unresolved source span")
        spans[ref] = document.text[item.start_offset : item.end_offset]
    if len({fact.fact_id for fact in data.verified_facts}) != len(data.verified_facts):
        raise ValueError("duplicate fact")
    for fact in data.verified_facts:
        if (
            any(
                ref not in evidence or evidence[ref].place_id != fact.place_id
                for ref in fact.evidence_ids
            )
            or not _safe_atomic_text(fact.text)
            or not is_safe_proposal_text(fact.time_scope)
            or any(fact.text != spans[ref] for ref in fact.evidence_ids)
            or (fact.time_scope != "TIMELESS" and fact.time_scope not in fact.text)
            or (
                fact.relation is not None
                and fact.place_id
                not in {
                    fact.relation.subject_id,
                    fact.relation.object_id,
                }
            )
            or (fact.support_type == "VERIFIED_RELATION") != (fact.relation is not None)
            or (fact.kind.value == "PREFERENCE") != (fact.support_type == "CONDITIONAL_PREFERENCE")
            or (fact.kind.value == "INTERPRETATION") != (fact.support_type == "INTERPRETATION")
            or fact.kind.value == "CONNECTOR"
        ):
            raise ValueError("fact lacks reviewed source support")


def validate_output(
    output: ModelProposal,
    data: GenerationInput,
) -> tuple[tuple[PlaceClaims, ...], tuple[Claim, ...], int]:
    claims = [claim for place in output.places for claim in place.reason_claims]
    claims.extend(output.summary_claims)
    if (
        len({place.place_id for place in output.places}) != len(output.places)
        or len({claim.claim_id for claim in claims}) != len(claims)
        or len(claims) > 24
        or sum(len(claim.text) for claim in claims) > 6000
        or any(not _safe_atomic_text(claim.text) for claim in claims)
        or any(place.place_id not in data.evidence_set.allowed_place_ids for place in output.places)
    ):
        raise ValueError("invalid proposal structure")
    facts = {fact.fact_id: fact for fact in data.verified_facts}
    held = 0
    used: set[str] = set()

    def checked(claim: ProposedClaim, place_id: str | None) -> Claim | None:
        nonlocal held
        fact = facts.get(claim.fact_id)
        if not _matches(claim, fact, place_id) or claim.fact_id in used:
            held += 1
            return None
        used.add(claim.fact_id)
        return Claim.model_validate(claim.model_dump(by_alias=True, exclude={"fact_id"}))

    places = []
    for place in output.places:
        reasons = tuple(
            valid
            for claim in place.reason_claims
            if (valid := checked(claim, place.place_id)) is not None
        )
        if reasons:
            places.append(
                PlaceClaims.model_validate({"placeId": place.place_id, "reasonClaims": reasons})
            )
    retained_places = {place.place_id for place in places}
    summary = []
    for claim in output.summary_claims:
        fact = facts.get(claim.fact_id)
        if fact is None or fact.place_id not in retained_places:
            held += 1
            continue
        valid = checked(claim, None)
        if valid is not None:
            summary.append(valid)
    if not places:
        raise ValueError("no supported place claims")
    return tuple(places), tuple(summary), held


def _matches(claim: ProposedClaim, fact: VerifiedFact | None, place_id: str | None) -> bool:
    return (
        fact is not None
        and (place_id is None or fact.place_id == place_id)
        and claim.text == fact.text
        and claim.kind == fact.kind
        and claim.evidence_ids == fact.evidence_ids
    )


def _safe_atomic_text(text: str) -> bool:
    normalized = unicodedata.normalize("NFKC", text)
    return (
        text == text.strip()
        and html.unescape(normalized) == normalized
        and is_safe_proposal_text(normalized)
        and not any(unicodedata.category(char).startswith("C") for char in text)
        and re.search(r"[.!?。！？]\s*\D", normalized) is None
    )
