from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.memory.sql_driver.sql_driver import SqlDriver


def _apply_prompt_schema(driver: 'SqlDriver') -> None:
    dialect = driver.dialect_
    auto_pk = dialect.auto_pk_

    ddl = f"""
    CREATE TABLE IF NOT EXISTS prompt (
        prompt_id     {auto_pk},
        kind          TEXT NOT NULL,
        task_id       INTEGER,
        role          TEXT,
        name          TEXT NOT NULL,
        body          TEXT NOT NULL,
        content_hash  TEXT NOT NULL,
        source_uri    TEXT,
        version       INTEGER NOT NULL DEFAULT 1,
        is_current    INTEGER NOT NULL DEFAULT 1,
        created_at    TEXT NOT NULL,
        UNIQUE (kind, task_id, role, name, version)
    );
    CREATE INDEX IF NOT EXISTS idx_prompt_lookup    ON prompt(kind, task_id, role, name, is_current);
    CREATE INDEX IF NOT EXISTS idx_prompt_task      ON prompt(task_id, is_current);
    CREATE INDEX IF NOT EXISTS idx_prompt_role_kind ON prompt(role, kind, is_current);
    """
    driver.executescript(ddl)
    driver.commit()
