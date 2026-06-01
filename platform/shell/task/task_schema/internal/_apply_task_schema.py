from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_driver.sql_driver import SqlDriver


def _apply_task_schema(driver: SqlDriver) -> None:
    dialect = driver.dialect_
    auto_pk = dialect.auto_pk_

    ddl = f"""
    CREATE TABLE IF NOT EXISTS task (
        task_id          {auto_pk},
        name             TEXT NOT NULL,
        version          INTEGER NOT NULL DEFAULT 1,
        content_hash     TEXT NOT NULL,
        body_md          TEXT NOT NULL,
        body_yaml_raw    TEXT NOT NULL,
        source_md_uri    TEXT,
        source_yaml_uri  TEXT,
        is_current       INTEGER NOT NULL DEFAULT 1,
        created_at       TEXT NOT NULL,
        UNIQUE (name, version)
    );
    CREATE INDEX IF NOT EXISTS idx_task_name_current ON task(name, is_current);
    CREATE INDEX IF NOT EXISTS idx_task_hash         ON task(content_hash);

    CREATE TABLE IF NOT EXISTS graph (
        graph_id        {auto_pk},
        task_id         INTEGER NOT NULL UNIQUE REFERENCES task(task_id) ON DELETE CASCADE,
        yaml_dict_json  TEXT NOT NULL,
        created_at      TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS graph_node (
        node_id          {auto_pk},
        graph_id         INTEGER NOT NULL REFERENCES graph(graph_id) ON DELETE CASCADE,
        position         INTEGER NOT NULL,
        node_dir         TEXT NOT NULL,
        runner_root_dir  TEXT,
        mode             TEXT NOT NULL,
        role             TEXT NOT NULL,
        type             TEXT NOT NULL,
        model            TEXT,
        command          TEXT,
        timeout          INTEGER,
        retries          INTEGER,
        log_level        TEXT,
        max_step         INTEGER,
        no_ask_user      INTEGER,
        autopilot        INTEGER,
        task_name        TEXT,
        source_dir       TEXT,
        work_dir         TEXT,
        status_initial   TEXT,
        extra_json       TEXT
    );
    CREATE INDEX IF NOT EXISTS idx_graph_node_graph_pos  ON graph_node(graph_id, position);
    CREATE INDEX IF NOT EXISTS idx_graph_node_graph_role ON graph_node(graph_id, role);
    """
    driver.executescript(ddl)
    driver.commit()
