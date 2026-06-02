from __future__ import annotations

from typing import TYPE_CHECKING

from shell.structure.node.node_port.internal._resolve_keys import (
    CONTEXT_TYPE_NODE_FILE,
    DIR_MARKER_KEY,
    _resolve_dir_scope,
)
from shell.utils.path.path import PathType

if TYPE_CHECKING:
    from shell.structure.node.node_port.db_node_port import DbNodePort


def _db_list_files(port: DbNodePort, path: PathType, suffix: str = "") -> list[PathType]:
    scope_id = _resolve_dir_scope(port, path)
    entries = port.memory_.list_entries(CONTEXT_TYPE_NODE_FILE, scope_id)
    suffix_lower = suffix.lower()
    results: list[PathType] = []
    for entry in entries:
        key = entry.get("entry_key") or entry.get("key")
        if key is None or key == DIR_MARKER_KEY:
            continue
        if suffix_lower and not key.lower().endswith(suffix_lower):
            continue
        results.append(path / key)
    return sorted(results)
