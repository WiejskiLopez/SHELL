from __future__ import annotations

from shell.memory.sql_driver.sql_driver import SqlDriver


_DDL = """
CREATE TABLE IF NOT EXISTS node_result (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id  TEXT,
    node_id      TEXT,
    session_id   TEXT,
    role         TEXT,
    mode         TEXT,
    status       TEXT,
    returncode   INTEGER,
    stdout       TEXT,
    stderr       TEXT,
    started_at   TEXT,
    stopped_at   TEXT,
    created_at   TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_node_result_workflow ON node_result(workflow_id);
CREATE INDEX IF NOT EXISTS idx_node_result_node     ON node_result(workflow_id, node_id);
"""


def _apply_node_result_schema(driver: SqlDriver) -> None:
    driver.executescript(_DDL)
    driver.commit()
