ALTER TABLE ai.revocation_state
    ADD COLUMN source_snapshot_watermark bigint CHECK (
        source_snapshot_watermark IS NULL OR source_snapshot_watermark >= 0
    );

CREATE TABLE ai.revocation_snapshot_staging_state (
    snapshot_id uuid PRIMARY KEY,
    watermark bigint NOT NULL CHECK (watermark >= 0),
    active_revision_id uuid NOT NULL,
    public_place_count bigint NOT NULL CHECK (public_place_count >= 0),
    event_cursor bigint NOT NULL DEFAULT 0 CHECK (event_cursor >= 0),
    place_cursor text NOT NULL DEFAULT '',
    events_complete boolean NOT NULL DEFAULT false,
    places_complete boolean NOT NULL DEFAULT false,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ai.revocation_snapshot_staging_events (
    snapshot_id uuid NOT NULL REFERENCES ai.revocation_snapshot_staging_state ON DELETE CASCADE,
    sequence bigint NOT NULL CHECK (sequence > 0),
    scope text NOT NULL CHECK (scope IN ('SOURCE_REVISION','PLACE')),
    source_type text,
    source_id text,
    source_revision text,
    place_id uuid,
    revoked_at timestamptz NOT NULL,
    reason_code text NOT NULL,
    PRIMARY KEY (snapshot_id, sequence),
    CHECK ((scope = 'PLACE' AND place_id IS NOT NULL AND source_type IS NULL
            AND source_id IS NULL AND source_revision IS NULL)
        OR (scope = 'SOURCE_REVISION' AND place_id IS NULL AND source_type IS NOT NULL
            AND source_id IS NOT NULL AND source_revision IS NOT NULL))
);

CREATE TABLE ai.revocation_snapshot_staging_places (
    snapshot_id uuid NOT NULL REFERENCES ai.revocation_snapshot_staging_state ON DELETE CASCADE,
    public_id text NOT NULL,
    PRIMARY KEY (snapshot_id, public_id)
);
