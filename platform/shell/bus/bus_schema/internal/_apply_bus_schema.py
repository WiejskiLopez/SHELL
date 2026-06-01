from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_driver.sql_driver import SqlDriver


def _apply_bus_schema(driver: SqlDriver) -> None:
    dialect = driver.dialect_
    auto_pk = dialect.auto_pk_

    ddl = f"""
    CREATE TABLE IF NOT EXISTS workflow (
        workflow_id        TEXT PRIMARY KEY,
        parent_workflow_id TEXT,
        root_task_id       TEXT,
        status             TEXT NOT NULL,
        started_at         TEXT NOT NULL,
        ended_at           TEXT,
        FOREIGN KEY (parent_workflow_id) REFERENCES workflow(workflow_id)
    );

    CREATE TABLE IF NOT EXISTS node_state (
        workflow_id      TEXT NOT NULL REFERENCES workflow(workflow_id) ON DELETE CASCADE,
        node_id          TEXT NOT NULL,
        role             TEXT,
        current_status   TEXT,
        last_envelope_id INTEGER,
        updated_at       TEXT NOT NULL,
        PRIMARY KEY (workflow_id, node_id)
    );

    CREATE TABLE IF NOT EXISTS envelope (
        id                  {auto_pk},
        workflow_id         TEXT NOT NULL REFERENCES workflow(workflow_id) ON DELETE CASCADE,
        parent_envelope_id  INTEGER REFERENCES envelope(id) ON DELETE SET NULL,
        correlation_id      TEXT,
        sender_node_id      TEXT,
        receiver_node_id    TEXT,
        source_role         TEXT NOT NULL,
        target_role         TEXT,
        sequence_id         INTEGER NOT NULL,
        step                INTEGER NOT NULL DEFAULT 0,
        status              TEXT NOT NULL,
        stage               TEXT NOT NULL,
        payload_json        TEXT NOT NULL,
        artifact_uri        TEXT,
        archive_uri         TEXT,
        created_at          TEXT NOT NULL,
        updated_at          TEXT NOT NULL,
        UNIQUE (workflow_id, sequence_id)
    );
    CREATE INDEX IF NOT EXISTS idx_env_workflow_stage  ON envelope(workflow_id, stage);
    CREATE INDEX IF NOT EXISTS idx_env_receiver_stage  ON envelope(receiver_node_id, stage);
    CREATE INDEX IF NOT EXISTS idx_env_target_stage    ON envelope(target_role, stage);
    CREATE INDEX IF NOT EXISTS idx_env_correlation     ON envelope(correlation_id);

    CREATE TABLE IF NOT EXISTS envelope_event (
        id            {auto_pk},
        envelope_id   INTEGER NOT NULL REFERENCES envelope(id) ON DELETE CASCADE,
        event_type    TEXT NOT NULL,
        from_value    TEXT,
        to_value      TEXT,
        source        TEXT,
        payload_json  TEXT,
        timestamp     TEXT NOT NULL
    );
    CREATE INDEX IF NOT EXISTS idx_event_envelope ON envelope_event(envelope_id, id);
    """
    driver.executescript(ddl)
    driver.commit()
