"""W7 deterministic query interpretation and plan proposals (no execution)."""
from .dictionary import DICTIONARY_VERSION, RULES_VERSION, CatalogEntry
from .normalization import normalize_query
from .planner import QueryPlanner

__all__ = ["CatalogEntry", "DICTIONARY_VERSION", "RULES_VERSION", "QueryPlanner", "normalize_query"]
