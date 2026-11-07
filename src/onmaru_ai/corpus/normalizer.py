"""Normalize public source bodies while retaining ranges into the received body."""

from __future__ import annotations

import html
import re
import unicodedata
from dataclasses import dataclass

_DISCARDED = re.compile(r"(?is)<(script|style)\b[^>]*>(?:.*?</\1\s*>|.*\Z)")
_TOKEN = re.compile(r"(?is)<[^>]*>|&(?:#\d+|#x[0-9a-f]+|[a-z][a-z0-9]+);|[^<&]+|[<&]")
_TAG_NAME = re.compile(r"(?is)</?\s*([a-z0-9]+)")
_BLOCK_TAGS = frozenset(
    {
        "address", "article", "aside", "blockquote", "br", "div", "footer",
        "h1", "h2", "h3", "h4", "h5", "h6", "header", "li", "main", "nav",
        "p", "pre", "section", "table", "tr",
    }
)


@dataclass(frozen=True)
class NormalizedSourceText:
    text: str
    # Each normalized character points to a half-open range in the received body.
    source_offsets: tuple[tuple[int, int], ...]

    def source_range(self, start: int, end: int) -> tuple[int, int]:
        if start < 0 or end <= start or end > len(self.text):
            raise ValueError("NORMALIZED_RANGE_INVALID")
        return self.source_offsets[start][0], self.source_offsets[end - 1][1]

    def provider_envelope(self) -> dict[str, str]:
        """Return data, never a provider role/message object.

        The generation layer remains responsible for serializing this value under its
        fixed prompt template. Source text cannot select a role or add provider fields.
        """

        return {"contentType": "UNTRUSTED_SOURCE_TEXT", "text": self.text}


class SourceTextNormalizer:
    """Strip executable markup, normalize Unicode/space, and retain source offsets."""

    def normalize(self, source: str) -> NormalizedSourceText:
        discarded = tuple((match.start(), match.end()) for match in _DISCARDED.finditer(source))
        raw: list[tuple[str, int, int]] = []
        discarded_index = 0
        for match in _TOKEN.finditer(source):
            while (
                discarded_index < len(discarded)
                and discarded[discarded_index][1] <= match.start()
            ):
                discarded_index += 1
            if (
                discarded_index < len(discarded)
                and discarded[discarded_index][0] <= match.start() < discarded[discarded_index][1]
            ):
                continue
            value = match.group()
            if value.startswith("<") and value.endswith(">"):
                tag = _TAG_NAME.match(value)
                if tag is not None and tag.group(1).lower() in _BLOCK_TAGS:
                    raw.append(("\n", match.start(), match.end()))
                continue
            if value.startswith("&") and value.endswith(";"):
                for character in unicodedata.normalize("NFC", html.unescape(value)):
                    raw.append((character, match.start(), match.end()))
            else:
                for run in re.finditer(r"\s+|\S+", value):
                    run_start = match.start() + run.start()
                    run_end = match.start() + run.end()
                    for character in unicodedata.normalize("NFC", run.group()):
                        raw.append((character, run_start, run_end))

        output: list[str] = []
        offsets: list[tuple[int, int]] = []
        whitespace: list[tuple[str, int, int]] = []

        def flush_whitespace() -> None:
            if not whitespace or not output:
                whitespace.clear()
                return
            separator = "\n" if any(char == "\n" for char, _, _ in whitespace) else " "
            if output[-1] != "\n" and not (output[-1] == " " and separator == " "):
                output.append(separator)
                offsets.append((whitespace[0][1], whitespace[-1][2]))
            whitespace.clear()

        for character, start, end in raw:
            if character.isspace():
                whitespace.append((character, start, end))
                continue
            flush_whitespace()
            output.append(character)
            offsets.append((start, end))
        # Trailing source whitespace and closing tags are intentionally outside the range.
        return NormalizedSourceText(text="".join(output), source_offsets=tuple(offsets))
