from __future__ import annotations

from shell.memory.sql_driver.sql_driver import SqlDriver


_DDL = """
CREATE TABLE IF NOT EXISTS runner_config (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    package_name  TEXT NOT NULL,
    kind          TEXT NOT NULL,
    body_yaml_raw TEXT NOT NULL,
    content_hash  TEXT NOT NULL,
    source_uri    TEXT,
    version       INTEGER NOT NULL DEFAULT 1,
    is_current    INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (package_name, kind, version)
);
CREATE INDEX IF NOT EXISTS idx_runcfg_current ON runner_config(package_name, kind, is_current);
CREATE INDEX IF NOT EXISTS idx_runcfg_hash    ON runner_config(content_hash);
"""


def _apply_runner_config_schema(driver: SqlDriver) -> None:
    driver.executescript(_DDL)
    driver.commit()
