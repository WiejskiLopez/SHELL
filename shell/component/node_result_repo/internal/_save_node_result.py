from __future__ import annotations

from datetime import datetime, timezone


def _save_node_result(
    repo,
    workflow_id: str | None,
    node_id: str | None,
    session_id: str | None,
    role: str | None,
    mode: str | None,
    status: str | None,
    returncode: int | None,
    stdout: str | None,
    stderr: str | None,
    started_at: str | None,
    stopped_at: str | None,
) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    sql = (
        "INSERT INTO node_result "
        "(workflow_id, node_id, session_id, role, mode, status, returncode, "
        " stdout, stderr, started_at, stopped_at, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    repo._driver.execute(sql, (
        workflow_id, node_id, session_id, role, mode, status, returncode,
        stdout, stderr, started_at, stopped_at, created_at,
    ))
    repo._driver.commit()
    return repo._driver.last_insert_id()
