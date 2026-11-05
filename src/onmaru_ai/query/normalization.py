"""Lossless local normalization, with conservative defense after Spring's privacy gate."""
import re
import unicodedata

PUNCTUATION = str.maketrans({"“": '"', "”": '"', "‘": "'", "’": "'", "？": "?", "！": "!"})
SENSITIVE = re.compile(
    r"https?://|www\.|[\w.+-]+\s*@\s*[\w.-]+|"
    r"(?:\d[\s-]*){7,}|(?:api[_ -]?key|secret|token|password)\s*[:=]|sk-[\w-]+",
    re.IGNORECASE,
)
OUT_OF_SCOPE = re.compile(
    r"오늘|내일|지금|실시간|영업|날씨|주가|예약|가격|입장료|교통편|버스|기차|항공|"
    r"\d{4}년|\d{1,2}월|\d{1,2}일"
)


def normalize_query(query: str) -> str:
    """Preserve every word, number, negation and quoted name in normalized order."""
    return " ".join(unicodedata.normalize("NFC", query).translate(PUNCTUATION).split())
