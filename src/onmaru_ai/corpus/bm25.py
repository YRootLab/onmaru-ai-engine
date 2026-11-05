"""Deterministic Korean lexical tokenization and BM25 scoring."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass

_TOKEN = re.compile(r"[0-9A-Za-z가-힣]+")
_PARTICLES = tuple(
    sorted(
        (
            "으로부터",
            "에게서",
            "에서는",
            "으로는",
            "까지는",
            "부터는",
            "이라는",
            "이라면",
            "으로",
            "에서",
            "에게",
            "한테",
            "께서",
            "부터",
            "까지",
            "처럼",
            "보다",
            "와",
            "과",
            "은",
            "는",
            "이",
            "가",
            "을",
            "를",
            "의",
            "에",
            "도",
            "만",
            "로",
        ),
        key=len,
        reverse=True,
    )
)


@dataclass(frozen=True)
class KoreanTokenizer:
    """Small versioned fallback tokenizer for names and whitespace-delimited Korean text.

    This is intentionally not presented as a morphological analyzer. The production
    extension/tokenizer remains a release gate; this profile provides deterministic
    query normalization and a portable BM25 reference implementation.
    """

    version: str = "ko-simple-particle-v1"

    def tokenize(self, text: str) -> tuple[str, ...]:
        normalized = unicodedata.normalize("NFKC", text).casefold()
        return tuple(self._strip_particle(token) for token in _TOKEN.findall(normalized))

    @staticmethod
    def _strip_particle(token: str) -> str:
        # ``마을`` is a frequent place-name noun, not a stem followed by object particle.
        # A compact fallback tokenizer must preserve this lexical ending rather than
        # pretend it can resolve every Korean morphological ambiguity.
        if token.endswith("마을"):
            return token
        for particle in _PARTICLES:
            if token.endswith(particle) and len(token) > len(particle) + 1:
                return token[: -len(particle)]
        return token


@dataclass(frozen=True)
class KoreanBm25:
    k1: float = 1.2
    b: float = 0.75

    def __post_init__(self) -> None:
        if self.k1 <= 0 or not 0 <= self.b <= 1:
            raise ValueError("invalid BM25 parameters")

    def score(
        self,
        query_tokens: Sequence[str],
        documents: Sequence[Sequence[str]],
    ) -> tuple[float, ...]:
        if not documents:
            return ()
        lengths = tuple(len(document) for document in documents)
        average_length = sum(lengths) / len(lengths) or 1.0
        document_frequencies = Counter(
            term for term in set(query_tokens) for document in documents if term in document
        )
        scores: list[float] = []
        for document, length in zip(documents, lengths, strict=True):
            frequencies = Counter(document)
            score = 0.0
            for term in set(query_tokens):
                frequency = frequencies[term]
                if frequency == 0:
                    continue
                doc_frequency = document_frequencies[term]
                inverse_frequency = math.log(
                    1 + (len(documents) - doc_frequency + 0.5) / (doc_frequency + 0.5)
                )
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * length / average_length
                )
                score += inverse_frequency * frequency * (self.k1 + 1) / denominator
            scores.append(score)
        return tuple(scores)
