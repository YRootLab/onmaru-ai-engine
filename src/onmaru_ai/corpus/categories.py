"""Approved canonical categories for OnMaru AI Engine corpus ingestion."""

from __future__ import annotations

from typing import Final

# 12 canonical categories approved for OnMaru public place and corpus indexing.
APPROVED_CANONICAL_CATEGORIES: Final[frozenset[str]] = frozenset({
    "HANOK",
    "HANOK_STAY",
    "HANOK_CAFE",
    "HANOK_EXPERIENCE",
    "TRADITIONAL_MARKET",
    "HISTORIC_SITE",
    "CULTURE_ART",
    "TRADITIONAL_FOOD",
    "GARDEN_ECOLOGY",
    "LOCAL_SCENE",
    "NATURE_SITE",
    "LEISURE_ACTIVITY",
})


def is_approved_category(category_code: str) -> bool:
    """Checks whether the category code is one of the 12 approved OnMaru canonical categories."""
    if not category_code:
        return False
    return category_code.strip().upper() in APPROVED_CANONICAL_CATEGORIES
