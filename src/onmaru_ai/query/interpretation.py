"""Conservative span interpretation. Unknown meaning never becomes generic retrieval."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

from onmaru_ai.contracts.models import CanonicalField, HardFilters, SafeQueryRequest
from onmaru_ai.contracts.vocabulary import ConceptCode

from .dictionary import CatalogEntry, Mention, match_mentions
from .normalization import OUT_OF_SCOPE, SENSITIVE, normalize_query

Operation = Literal["RECOMMEND", "EXPLAIN", "COMPARE", "REFINE"]
ClarifyReason = Literal[
    "AMBIGUOUS_TARGET", "CONFLICTING_CONDITIONS", "UNSUPPORTED_SCOPE", "SEMANTIC_LOSS"
]


class InterpretationError(Exception):
    def __init__(self, reason: ClarifyReason) -> None:
        self.reason = reason
        super().__init__(reason)


@dataclass(frozen=True)
class Interpretation:
    text: str
    operation: Operation
    targets: tuple[str, ...]
    positive: tuple[ConceptCode, ...]
    negative: tuple[ConceptCode, ...]
    fields: tuple[CanonicalField, ...]
    filters: HardFilters
    has_body: bool
    has_negation: bool


FIELD_ALIASES: dict[CanonicalField, tuple[str, ...]] = {
    "PUBLIC_ADDRESS": ("주소", "위치"),
    "REGION_CODE": ("어느 지역",),
    "CATEGORY_CODE": ("분류", "종류"),
    "PUBLIC_STATUS": ("현재 볼 수 있는지", "공개 여부"),
}
NEGATION = re.compile(r"말고|제외|빼(?:고|줘|주세요)?|싫")
ADJECTIVE_NEGATION = re.compile(r"하지 않|하지않|지 않은|지 않|안\s|아닌|없[는어]")
REFERENCE = re.compile(
    r"첫\s*번째(?:\s*장소)?[가는은]?|두\s*번째(?:\s*장소)?[가는은]?|여기|이곳|그건"
)
# Each complete grammar token is accounted for after semantic spans are removed.
# Extending this list requires new reviewed golds. It is not a stop-word remover:
# the original accepted text is retained verbatim as semanticQuery.
GRAMMAR = re.compile(
    r"(?:알려\s*줘|알려주세요|알려|추천해줘|추천|가볼 만한|갈|곳|장소|명소|"
    r"이야기도|이야기|설명해줘|설명|왜|어떤 의미|관련 있나요|관련|있나요|"
    r"비교와|비교|차이와|차이|바꿔줘|바꿔|말고|빼고|빼줘|빼주세요|제외|"
    r"넣어줘|넣어|꼭|추가|유지하고|유지|고정|조건 완화|또는|그리고|"
    r"주변|전국|지역 무관|상관없이|도|와|과|은|는|을|를|가|의|만|에서|에|"
    r"[1-5]\s*곳)(?=$|\s|[\"'.,!?])"
)


def _unique[T](values: list[T] | tuple[T, ...]) -> tuple[T, ...]:
    return tuple(dict.fromkeys(values))


def _erase(text: str, spans: list[tuple[int, int]]) -> str:
    chars = list(text)
    for start, end in spans:
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def _negative(text: str, mention: Mention, next_start: int) -> bool:
    return bool(NEGATION.search(text[mention.end:next_start]))


def _resolve_place(mention: Mention, regions: tuple[str, ...], request: SafeQueryRequest,
                   catalog: tuple[CatalogEntry, ...]) -> str:
    options = mention.codes
    if len(options) > 1 and regions:
        options = tuple(code for code in options if any(
            entry.code == code and entry.region_code in regions for entry in catalog))
    if len(options) > 1:
        confirmed = request.confirmed_context.last_confirmed_place_ids
        options = tuple(code for code in options if code in confirmed)
    if len(options) != 1:
        raise InterpretationError("AMBIGUOUS_TARGET")
    return options[0]


def _narrow(upper: tuple[str, ...] | None, selected: tuple[str, ...]) -> tuple[str, ...] | None:
    if not selected:
        return upper
    if upper is not None and not set(selected) <= set(upper):
        raise InterpretationError("UNSUPPORTED_SCOPE")
    return selected


def interpret(request: SafeQueryRequest, catalog: tuple[CatalogEntry, ...]) -> Interpretation:
    text = normalize_query(request.safe_query)
    if not text or len(text) > 240 or SENSITIVE.search(text):
        raise InterpretationError("SEMANTIC_LOSS")
    if OUT_OF_SCOPE.search(text):
        raise InterpretationError("UNSUPPORTED_SCOPE")
    if ADJECTIVE_NEGATION.search(text):
        raise InterpretationError("SEMANTIC_LOSS")
    mentions = match_mentions(text, catalog)
    spans = [(m.start, m.end) for m in mentions]
    marked = [(m, _negative(text, m, mentions[i + 1].start if i + 1 < len(mentions)
                           else len(text))) for i, m in enumerate(mentions)]
    regions = _unique([code for m, neg in marked if m.kind == "REGION" and not neg
                       for code in m.codes])
    if len(regions) > 2 or (len(regions) > 1 and "또는" not in text):
        raise InterpretationError("CONFLICTING_CONDITIONS")
    if not regions and request.confirmed_context.region_code:
        regions = (request.confirmed_context.region_code,)
    positive = _unique([ConceptCode(code) for m, neg in marked if m.kind == "CONCEPT" and not neg
                        for code in m.codes])
    negative = _unique([ConceptCode(code) for m, neg in marked if m.kind == "CONCEPT" and neg
                        for code in m.codes])
    if set(positive) & set(negative):
        raise InterpretationError("CONFLICTING_CONDITIONS")
    if len(positive) > 4 or len(negative) > 2:
        raise InterpretationError("SEMANTIC_LOSS")
    targets: list[str] = []
    excluded = list(request.confirmed_context.excluded_place_ids)
    pinned = list(request.confirmed_context.pinned_place_ids)
    for m, neg in marked:
        if m.kind == "PLACE":
            code = _resolve_place(m, regions, request, catalog)
            if neg:
                excluded.append(code)
                pinned = [pin for pin in pinned if pin != code]
            else:
                targets.append(code)
    for ref in REFERENCE.finditer(text):
        spans.append(ref.span())
        cards = request.confirmed_context.last_confirmed_place_ids
        ordinal = 0 if ref.group().startswith("첫") else 1
        if "번째" not in ref.group():
            if len(cards) != 1:
                raise InterpretationError("AMBIGUOUS_TARGET")
            ordinal = 0
        if ordinal >= len(cards):
            raise InterpretationError("AMBIGUOUS_TARGET")
        target = cards[ordinal]
        end = next((m.start for m in mentions if m.start >= ref.end()), len(text))
        if NEGATION.search(text[ref.end():end]):
            excluded.append(target)
            pinned = [pin for pin in pinned if pin != target]
        else:
            targets.append(target)
    target_ids = _unique(targets)
    if len(target_ids) > 2:
        raise InterpretationError("AMBIGUOUS_TARGET")
    fields: list[CanonicalField] = []
    for field, aliases in FIELD_ALIASES.items():
        for alias in aliases:
            for match in re.finditer(r"(?<!\w)" + re.escape(alias) + r"(?:도|와|과|는|를)?(?=$|\W)",
                                     text):
                fields.append(field)
                spans.append(match.span())
    canonical = _unique(fields)
    compare = bool(re.search(r"비교|차이", text))
    recommend = bool(re.search(r"추천|가볼 만한", text))
    explain = bool(re.search(r"이야기|설명|왜|관련|역사|유래|건축", text))
    if compare + recommend + explain > 1:
        raise InterpretationError("CONFLICTING_CONDITIONS")
    if compare:
        operation: Operation = "COMPARE"
    elif NEGATION.search(text) or re.search(r"유지|고정|바꿔|추가|넣어", text):
        operation = "REFINE"
    elif explain or (target_ids and not recommend) or canonical:
        operation = "EXPLAIN"
    else:
        operation = "RECOMMEND"
    has_body = bool(positive or negative or compare or recommend or explain or not canonical)
    if canonical and (not target_ids or len(target_ids) > 1):
        raise InterpretationError("CONFLICTING_CONDITIONS" if target_ids else "AMBIGUOUS_TARGET")
    if has_body and len(canonical) > 1:
        raise InterpretationError("CONFLICTING_CONDITIONS")
    if not canonical and not positive and not negative and not target_ids:
        raise InterpretationError("SEMANTIC_LOSS")
    remainder = _erase(text, spans)
    remainder = GRAMMAR.sub(" ", remainder)
    if re.sub(r"[\s\"'.,!?]", "", remainder):
        raise InterpretationError("SEMANTIC_LOSS")
    bounds = request.authority_bounds.filters
    pinned_ids = _unique([*bounds.pinned_place_ids, *pinned])
    excluded_ids = _unique([*bounds.excluded_place_ids, *excluded])
    if set(pinned_ids) & set(excluded_ids) or set(target_ids) & set(excluded_ids):
        raise InterpretationError("CONFLICTING_CONDITIONS")
    if any(field not in request.authority_bounds.allowed_canonical_fields for field in canonical):
        raise InterpretationError("UNSUPPORTED_SCOPE")
    if () in (bounds.place_ids, bounds.region_codes, bounds.category_codes):
        raise InterpretationError("UNSUPPORTED_SCOPE")
    place_ids = _narrow(bounds.place_ids, _unique([*target_ids, *pinned_ids]))
    category_codes = _unique([code for m, neg in marked if m.kind == "CATEGORY" and not neg
                              for code in m.codes])
    filters = HardFilters.model_validate({
        **bounds.model_dump(by_alias=True),
        "placeIds": place_ids,
        "regionCodes": _narrow(bounds.region_codes, regions),
        "categoryCodes": _narrow(bounds.category_codes, category_codes),
        "pinnedPlaceIds": pinned_ids, "excludedPlaceIds": excluded_ids,
    })
    return Interpretation(text, operation, target_ids, positive, negative, canonical, filters,
                          has_body, bool(NEGATION.search(text)))
