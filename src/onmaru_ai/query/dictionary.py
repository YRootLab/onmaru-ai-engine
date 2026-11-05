"""Reviewed local questions-1 vocabulary; catalog identities come from a trusted snapshot."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from onmaru_ai.contracts.models import Identifier
from onmaru_ai.contracts.vocabulary import ConceptCode

DICTIONARY_VERSION = "questions-1"
RULES_VERSION = "query-rules-1"


class CatalogEntry(BaseModel):
    """Trusted public catalog input, never constructed from a user's free text.

    The caller pins this snapshot to the request's corpus/config versions. A catalog
    entry describes identity, not current authorization; authority bounds still apply.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")
    code: Identifier
    kind: Literal["PLACE", "REGION", "CATEGORY"]
    display_label: str = Field(min_length=1, max_length=120)
    synonyms: tuple[str, ...] = ()
    search_aliases: tuple[str, ...] = ()
    status: Literal["ACTIVE", "RETIRED"] = "ACTIVE"
    region_code: Identifier | None = None
    category_code: Identifier | None = None
    concept_codes: tuple[ConceptCode, ...] = ()


# Longest spans win. Family suitability intentionally maps to one concept instead
# of spending the bounded wire concept slots on duplicate companion/focus labels.
CONCEPT_ALIASES: dict[ConceptCode, tuple[str, ...]] = {
    ConceptCode.HISTORY: ("역사", "유래"),
    ConceptCode.HISTORICAL_SIGNIFICANCE: ("역사적 의미", "역사적 관련"),
    ConceptCode.ARCHITECTURE: ("건축", "구조"),
    ConceptCode.CULTURAL_PRACTICE: ("전통", "체험"),
    ConceptCode.VISIT_POINT: ("볼거리", "방문 포인트"),
    ConceptCode.FAMILY_SUITABILITY: ("아이와", "가족", "아이와 갈"),
    ConceptCode.QUIETNESS: ("고요함",),
    ConceptCode.ACCESSIBILITY: ("접근성", "무장애", "휠체어"),
    ConceptCode.INDEPENDENCE_MOVEMENT: ("독립운동", "독립운동가"),
    ConceptCode.JOSEON_PERIOD: ("조선시대", "조선"),
    ConceptCode.TRADITIONAL_MARKET: ("전통시장", "재래시장", "시장"),
    ConceptCode.HANOK: ("한옥", "고택"),
    ConceptCode.K_CONTENT: ("촬영지", "작품 관련 장소"),
    ConceptCode.SOLO: ("혼자",),
    ConceptCode.COUPLE: ("연인", "둘이"),
    ConceptCode.FRIENDS: ("친구와",),
    ConceptCode.QUIET: ("조용한", "한적한"),
    ConceptCode.LIVELY: ("활기찬", "북적이는"),
    ConceptCode.WALKABLE: ("걷기 좋은", "산책", "걷고 싶어"),
}
EXACT_CONCEPTS = frozenset({
    ConceptCode.INDEPENDENCE_MOVEMENT, ConceptCode.JOSEON_PERIOD,
    ConceptCode.TRADITIONAL_MARKET, ConceptCode.HANOK, ConceptCode.K_CONTENT,
})

# A suffix must consume the rest of its word, preventing 한옥마을맛집 -> 한옥.
PARTICLES = r"(?:에서|으로|에게|은|는|을|를|의|과|와|이|가|도|만|에|로|은요|는요)*"
BOUNDARY = r"(?=$|[\s\"'.,!?，。·()])"


@dataclass(frozen=True)
class Mention:
    start: int
    end: int
    kind: str
    codes: tuple[str, ...]


def match_mentions(text: str, catalog: tuple[CatalogEntry, ...]) -> tuple[Mention, ...]:
    aliases: dict[tuple[str, str], list[str]] = {}
    for code, words in CONCEPT_ALIASES.items():
        for word in words:
            aliases.setdefault((word, "CONCEPT"), []).append(code.value)
    for entry in catalog:
        if entry.status != "ACTIVE":
            continue
        for word in (entry.display_label, *entry.synonyms):
            aliases.setdefault((word, entry.kind), []).append(entry.code)
    candidates: list[Mention] = []
    for (alias, kind), codes in aliases.items():
        pattern = re.compile(r"(?<![\w])" + re.escape(alias) + PARTICLES + BOUNDARY)
        candidates.extend(Mention(m.start(), m.end(), kind, tuple(dict.fromkeys(codes)))
                          for m in pattern.finditer(text))
    # Greedy longest match globally, followed by text order. Stable ties do not
    # silently select between a catalog identity and a concept of the same name.
    chosen: list[Mention] = []
    for item in sorted(candidates, key=lambda m: (-(m.end - m.start), m.start)):
        if not any(item.start < old.end and old.start < item.end for old in chosen):
            chosen.append(item)
    return tuple(sorted(chosen, key=lambda m: m.start))
