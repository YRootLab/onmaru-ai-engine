"""Closed W0 vocabularies, sourced from the versioned AI-RAG design documents."""

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType


class ConceptCode(StrEnum):
    """Searchable concepts from question-understanding.md's initial code table."""

    HISTORY = "HISTORY"
    HISTORICAL_SIGNIFICANCE = "HISTORICAL_SIGNIFICANCE"
    ARCHITECTURE = "ARCHITECTURE"
    CULTURAL_PRACTICE = "CULTURAL_PRACTICE"
    VISIT_POINT = "VISIT_POINT"
    FAMILY_SUITABILITY = "FAMILY_SUITABILITY"
    QUIETNESS = "QUIETNESS"
    ACCESSIBILITY = "ACCESSIBILITY"
    INDEPENDENCE_MOVEMENT = "INDEPENDENCE_MOVEMENT"
    JOSEON_PERIOD = "JOSEON_PERIOD"
    TRADITIONAL_MARKET = "TRADITIONAL_MARKET"
    HANOK = "HANOK"
    K_CONTENT = "K_CONTENT"
    SOLO = "SOLO"
    COUPLE = "COUPLE"
    FAMILY = "FAMILY"
    FRIENDS = "FRIENDS"
    QUIET = "QUIET"
    LIVELY = "LIVELY"
    WALKABLE = "WALKABLE"


# A new dictionary must be registered explicitly, with matching schema and fixtures.
QUESTION_DICTIONARIES: Mapping[str, frozenset[ConceptCode]] = MappingProxyType(
    {"questions-1": frozenset(ConceptCode)}
)


class PlanReasonCode(StrEnum):
    """Fixed reason IDs for the routing/clarification cases in query-processing.md."""

    CANONICAL_FACT_ONLY = "CANONICAL_FACT_ONLY"
    EXACT_PUBLIC_TERM = "EXACT_PUBLIC_TERM"
    SINGLE_SEMANTIC_TOPIC = "SINGLE_SEMANTIC_TOPIC"
    COMPOSITE_QUERY = "COMPOSITE_QUERY"
    CANONICAL_FACT_WITH_RETRIEVAL = "CANONICAL_FACT_WITH_RETRIEVAL"
    AMBIGUOUS_TARGET = "AMBIGUOUS_TARGET"
    CONFLICTING_CONDITIONS = "CONFLICTING_CONDITIONS"
    UNSUPPORTED_SCOPE = "UNSUPPORTED_SCOPE"
    SEMANTIC_LOSS = "SEMANTIC_LOSS"


class ClarificationQuestionCode(StrEnum):
    """Fixed Spring renderer IDs for the four clarification reasons."""

    CHOOSE_TARGET = "CHOOSE_TARGET"
    RESOLVE_CONDITIONS = "RESOLVE_CONDITIONS"
    SUPPORTED_TRAVEL_SCOPE = "SUPPORTED_TRAVEL_SCOPE"
    PRESERVE_MEANING = "PRESERVE_MEANING"


CLARIFICATION_QUESTIONS: Mapping[str, ClarificationQuestionCode] = MappingProxyType(
    {
        "AMBIGUOUS_TARGET": ClarificationQuestionCode.CHOOSE_TARGET,
        "CONFLICTING_CONDITIONS": ClarificationQuestionCode.RESOLVE_CONDITIONS,
        "UNSUPPORTED_SCOPE": ClarificationQuestionCode.SUPPORTED_TRAVEL_SCOPE,
        "SEMANTIC_LOSS": ClarificationQuestionCode.PRESERVE_MEANING,
    }
)


class ClaimKind(StrEnum):
    """The four claim kinds from grounding-and-review.md's output contract."""

    FACT = "FACT"
    INTERPRETATION = "INTERPRETATION"
    PREFERENCE = "PREFERENCE"
    CONNECTOR = "CONNECTOR"


class FailureStage(StrEnum):
    """Failure decision table in request-lifecycle.md; distinct from progress."""

    REQUEST = "REQUEST"
    INTERPRETATION = "INTERPRETATION"
    PLANNING = "PLANNING"
    ROUTING = "ROUTING"
    QUOTA = "QUOTA"
    RETRIEVAL = "RETRIEVAL"
    RETRIEVAL_EMPTY = "RETRIEVAL_EMPTY"
    GENERATION = "GENERATION"
    VALIDATION = "VALIDATION"
    DELIVERY = "DELIVERY"
