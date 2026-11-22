import json
from pathlib import Path

import psycopg
import pytest

from scripts.runtime_version import RuntimeVersionUnavailable, read_runtime_versions

MIGRATION = (
    Path(__file__).resolve().parents[2] / "migrations/ai/005_source_revocation_bootstrap.sql"
)


def test_runtime_version_print_contract_reads_active_versions_and_watermark(
    db: psycopg.Connection[tuple[object, ...]], dsn: str
) -> None:
    db.execute(MIGRATION.read_text(encoding="utf-8"))
    db.execute(
        """INSERT INTO ai.corpus_revisions
           (revision_id,manifest_hash,manifest,source_revision,state,embedding_profile_id,
            chunker_version,dictionary_version,config_hash,document_count,chunk_count,embedding_count)
           VALUES ('rev-runtime-test','hash-runtime-test',%s,'source-test','ACTIVE',
                   'profile-test','chunker-test','questions-1','config-runtime-test',0,0,0)""",
        (json.dumps({"revisionId": "rev-runtime-test"}),),
    )
    db.execute(
        "UPDATE ai.revocation_state SET sequence=7,source_snapshot_watermark=7,"
        "heartbeat_at=clock_timestamp() WHERE id=1"
    )
    db.execute(
        "UPDATE ai.active_corpus SET revision_id='rev-runtime-test',"
        "revocation_sequence=7 WHERE id=1"
    )

    result = read_runtime_versions(dsn)

    assert result.as_environment() == {
        "CORPUS_REVISION": "rev-runtime-test",
        "CONFIG_HASH": "config-runtime-test",
        "QUESTION_DICTIONARY_VERSION": "questions-1",
        "SOURCE_REVOCATION_SEQUENCE": "7",
    }


def test_runtime_version_refuses_stale_revocation_heartbeat(
    db: psycopg.Connection[tuple[object, ...]], dsn: str
) -> None:
    db.execute(MIGRATION.read_text(encoding="utf-8"))
    db.execute(
        """INSERT INTO ai.corpus_revisions
           (revision_id,manifest_hash,manifest,source_revision,state,embedding_profile_id,
            chunker_version,dictionary_version,config_hash,document_count,chunk_count,embedding_count)
           VALUES ('rev-runtime-test','hash-runtime-test',%s,'source-test','ACTIVE',
                   'profile-test','chunker-test','questions-1','config-runtime-test',0,0,0)""",
        (json.dumps({"revisionId": "rev-runtime-test"}),),
    )
    db.execute(
        "UPDATE ai.revocation_state SET sequence=0,source_snapshot_watermark=0,"
        "heartbeat_at=clock_timestamp()-interval '2 minutes' WHERE id=1"
    )
    db.execute(
        "UPDATE ai.active_corpus SET revision_id='rev-runtime-test',"
        "revocation_sequence=0 WHERE id=1"
    )

    with pytest.raises(RuntimeVersionUnavailable, match="heartbeat_stale"):
        read_runtime_versions(dsn)
