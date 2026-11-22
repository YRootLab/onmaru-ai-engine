from __future__ import annotations

from scripts.print_active_runtime_versions import read_active_versions


class Cursor:
    def __init__(self, row: dict[str, object] | None = None) -> None:
        self.row = row

    def fetchone(self) -> dict[str, object]:
        return self.row or {
            "revision_id": "rev-active",
            "config_hash": "sha256:" + "a" * 64,
            "dictionary_version": "questions-v1",
            "revocation_sequence": 4,
            "current_sequence": 4,
            "source_snapshot_watermark": 3,
            "heartbeat_at": "2026-11-20T00:00:00Z",
            "heartbeat_healthy": True,
            "approved_fact_count": 7,
        }


class Connection:
    def execute(self, statement: str) -> Cursor | None:
        if "SET TRANSACTION READ ONLY" in statement:
            return None
        assert "ai.reviewed_facts" in statement
        assert "heartbeat_healthy" in statement
        return Cursor()


def test_active_versions_include_review_and_revocation_readiness() -> None:
    values = read_active_versions(Connection())
    assert values["revision_id"] == "rev-active"
    assert values["approved_fact_count"] == 7
    assert values["heartbeat_healthy"] is True


def test_active_versions_reject_missing_source_snapshot() -> None:
    class MissingSnapshotConnection(Connection):
        def execute(self, statement: str) -> Cursor | None:
            if "SET TRANSACTION READ ONLY" in statement:
                return None
            row = Cursor().fetchone()
            row["source_snapshot_watermark"] = None
            return Cursor(row)

    try:
        read_active_versions(MissingSnapshotConnection())
    except ValueError as error:
        assert "snapshot" in str(error)
    else:
        raise AssertionError("missing source snapshot must block runtime version output")
