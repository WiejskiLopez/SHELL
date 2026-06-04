from __future__ import annotations

from datetime import datetime, timezone

from shell.component.runner_config_repo.internal._compute_runner_config_hash import _compute_runner_config_hash


def _import_runner_config_if_changed(
    repo,
    package_name: str,
    kind: str,
    body: str,
    source_uri: str | None,
) -> dict:
    content_hash = _compute_runner_config_hash(package_name, kind, body)
    rows = repo._driver.query(
        "SELECT id, version, content_hash, body_yaml_raw, source_uri "
        "FROM runner_config "
        "WHERE package_name = ? AND kind = ? AND is_current = 1 "
        "LIMIT 1",
        (package_name, kind),
    )
    if rows and rows[0]["content_hash"] == content_hash:
        return rows[0]
    next_version = 1
    if rows:
        next_version = int(rows[0]["version"]) + 1
        repo._driver.execute(
            "UPDATE runner_config SET is_current = 0 WHERE package_name = ? AND kind = ?",
            (package_name, kind),
        )
    created_at = datetime.now(timezone.utc).isoformat()
    repo._driver.execute(
        "INSERT INTO runner_config "
        "(package_name, kind, body_yaml_raw, content_hash, source_uri, version, is_current, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, 1, ?)",
        (package_name, kind, body, content_hash, source_uri, next_version, created_at),
    )
    repo._driver.commit()
    new_id = repo._driver.last_insert_id()
    return {
        "id": new_id,
        "version": next_version,
        "content_hash": content_hash,
        "body_yaml_raw": body,
        "source_uri": source_uri,
    }


def _get_current_runner_config(repo, package_name: str, kind: str) -> dict | None:
    rows = repo._driver.query(
        "SELECT id, version, content_hash, body_yaml_raw, source_uri "
        "FROM runner_config "
        "WHERE package_name = ? AND kind = ? AND is_current = 1 "
        "LIMIT 1",
        (package_name, kind),
    )
    return rows[0] if rows else None
