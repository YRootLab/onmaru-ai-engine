from __future__ import annotations

from scripts.export_reviewed_fact_candidates import iter_candidate_rows


class Cursor:
    def __init__(self) -> None:
        self.rows: list[dict[str, object]] = [
            {
                "chunk_id": "123e4567-e89b-12d3-a456-426614174000",
                "start_offset": 1,
                "chunk_text": "  한옥은 1930년에 지어졌다. 주변에 마당이 있다.",
                "place_id": "p-public-1",
                "normalized_text": "앞  한옥은 1930년에 지어졌다. 주변에 마당이 있다. 뒤",
            }
        ]

    def __enter__(self) -> Cursor:
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def execute(self, query: str, params: object) -> None:
        assert "r.state='ACTIVE'" in query
        assert params == ("rev-active",)

    def fetchmany(self, _size: int) -> list[dict[str, object]]:
        rows, self.rows = self.rows, []
        return rows


class Connection:
    def cursor(self, *, name: str) -> Cursor:
        assert name
        return Cursor()


def test_review_candidate_export_uses_exact_active_source_spans() -> None:
    candidates = list(iter_candidate_rows(Connection(), "rev-active"))
    assert [item["candidateText"] for item in candidates] == [
        "한옥은 1930년에 지어졌다.",
        "주변에 마당이 있다.",
    ]
    for item in candidates:
        start, end = item["startOffset"], item["endOffset"]
        assert item["reviewStatus"] == "NEEDS_HUMAN_REVIEW"
        assert isinstance(item["candidateId"], str)
        assert item["candidateId"].startswith("fc-")
        assert isinstance(start, int) and isinstance(end, int)
        assert end > start
