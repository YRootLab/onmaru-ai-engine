"""Outbound adapters owned by the AI engine."""

from .spring_place import (
    CanonicalPlaceProjection,
    PlaceLookupDisposition,
    PlaceLookupOutcome,
    SpringPlaceQueryAdapter,
)

__all__ = [
    "CanonicalPlaceProjection",
    "PlaceLookupDisposition",
    "PlaceLookupOutcome",
    "SpringPlaceQueryAdapter",
]
