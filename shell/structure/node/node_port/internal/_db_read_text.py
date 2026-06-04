from __future__ import annotations

from typing import TYPE_CHECKING

from shell.structure.node.node_port.internal._resolve_keys import (
    CONTEXT_TYPE_NODE_FILE,
    _resolve_file_keys,
)
from shell.utils.path.path import PathType

if TYPE_CHECKING:
    from shell.structure.node.node_port.db_node_port import DbNodePort


def _db_read_text(port: DbNodePort, path: PathType) -> str:
    scope_id, entry_key = _resolve_file_keys(port, path)
    entry = port.memory_.get_entry(CONTEXT_TYPE_NODE_FILE, scope_id, entry_key)
    if entry is None:
        raise FileNotFoundError(f"DbNodePort: no entry at scope='{scope_id}' key='{entry_key}'")
    value = entry.get("value", {}) or {}
    body = value.get("body")
    if body is None:
        raise ValueError(f"DbNodePort: entry at scope='{scope_id}' key='{entry_key}' missing 'body'")
    return body
