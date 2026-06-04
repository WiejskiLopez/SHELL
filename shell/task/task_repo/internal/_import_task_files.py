"""_import_task_files.py
Idempotent import of <name>.md + <name>.yaml from disk into the DB.

If a task row with (name, content_hash) already exists, returns the existing
record (no-op). Otherwise inserts a new task row with bumped version and
flips is_current pointer so the new row becomes the active one. Also creates
the graph + graph_node rows for the new task version.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import yaml

from shell.task.task_record import TaskRecord
from shell.task.task_repo.internal._compute_task_hash import _compute_task_hash
from shell.task.task_repo.internal._get_current_task import _get_current_task
from shell.task.task_repo.internal._row_to_task_record import _row_to_task_record
from shell.utils.path.path import Path

if TYPE_CHECKING:
    from shell.task.task_repo.task_repo import TaskRepo


def _import_task_files(
    repo: TaskRepo,
    name: str,
    source_md_path: str,
    source_yaml_path: str,
) -> TaskRecord:
    body_md = Path.read_text(Path.new(source_md_path))
    body_yaml_raw = Path.read_text(Path.new(source_yaml_path))
    content_hash = _compute_task_hash(body_md, body_yaml_raw)

    current = _get_current_task(repo, name)
    if current is not None and current.content_hash_ == content_hash:
        return current

    parsed = yaml.safe_load(body_yaml_raw) or {}
    graph_entries = parsed.get("graph", []) or []
    yaml_dict_json = json.dumps(parsed, ensure_ascii=False)

    next_version = 1 if current is None else (_max_version(repo, name) + 1)
    now = datetime.now(timezone.utc).isoformat()

    driver = repo.driver_
    driver.execute(
        "UPDATE task SET is_current = 0 WHERE name = ? AND is_current = 1",
        (name,),
    )
    driver.execute(
        """
        INSERT INTO task (name, version, content_hash, body_md, body_yaml_raw,
                          source_md_uri, source_yaml_uri, is_current, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (name, next_version, content_hash, body_md, body_yaml_raw,
         source_md_path, source_yaml_path, now),
    )
    task_id = driver.last_insert_id()

    driver.execute(
        """
        INSERT INTO graph (task_id, yaml_dict_json, created_at)
        VALUES (?, ?, ?)
        """,
        (task_id, yaml_dict_json, now),
    )
    graph_id = driver.last_insert_id()

    for position, entry in enumerate(graph_entries):
        _insert_graph_node(driver, graph_id, position, entry)

    driver.commit()

    rows = driver.query(
        """
        SELECT task_id, name, version, content_hash, body_md, body_yaml_raw,
               source_md_uri, source_yaml_uri, is_current, created_at
          FROM task WHERE task_id = ?
        """,
        (task_id,),
    )
    return _row_to_task_record(rows[0])


def _max_version(repo: TaskRepo, name: str) -> int:
    rows = repo.driver_.query(
        "SELECT COALESCE(MAX(version), 0) AS v FROM task WHERE name = ?",
        (name,),
    )
    return rows[0]["v"] if rows else 0


def _insert_graph_node(driver, graph_id: int, position: int, entry: dict) -> None:
    known_keys = {
        "node_dir", "runner_root_dir", "mode", "role", "type", "model",
        "command", "timeout", "retries", "log_level", "max_step",
        "no_ask_user", "autopilot", "task_name", "source_dir", "work_dir",
        "status",
    }
    extra = {k: v for k, v in entry.items() if k not in known_keys}
    extra_json = json.dumps(extra, ensure_ascii=False) if extra else None

    driver.execute(
        """
        INSERT INTO graph_node (
            graph_id, position, node_dir, runner_root_dir, mode, role, type,
            model, command, timeout, retries, log_level, max_step,
            no_ask_user, autopilot, task_name, source_dir, work_dir,
            status_initial, extra_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            graph_id,
            position,
            entry.get("node_dir"),
            entry.get("runner_root_dir"),
            entry.get("mode"),
            entry.get("role"),
            entry.get("type"),
            entry.get("model"),
            entry.get("command"),
            entry.get("timeout"),
            entry.get("retries"),
            entry.get("log_level"),
            entry.get("max_step"),
            int(entry["no_ask_user"]) if entry.get("no_ask_user") is not None else None,
            int(entry["autopilot"]) if entry.get("autopilot") is not None else None,
            entry.get("task_name"),
            entry.get("source_dir"),
            entry.get("work_dir"),
            entry.get("status"),
            extra_json,
        ),
    )
