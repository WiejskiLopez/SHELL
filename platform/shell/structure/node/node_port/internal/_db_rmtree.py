from __future__ import annotations

from typing import TYPE_CHECKING

from shell.structure.node.node_port.internal._resolve_keys import (
    CONTEXT_TYPE_NODE_FILE,
    _resolve_dir_scope,
)
from shell.utils.path.path import PathType

if TYPE_CHECKING:
    from shell.structure.node.node_port.db_node_port import DbNodePort


def _db_rmtree(port: DbNodePort, path: PathType) -> None:
    scope_id_prefix = _resolve_dir_scope(port, path)
    backend = port.memory_.backend_
    rows = backend.driver_.query(
        "SELECT scope_id, entry_key FROM context_entry "
        "WHERE context_type = ? AND (scope_id = ? OR scope_id LIKE ?)",
        (CONTEXT_TYPE_NODE_FILE, scope_id_prefix, scope_id_prefix + "/%"),
    )
    for row in rows:
        port.memory_.delete_entry(CONTEXT_TYPE_NODE_FILE, row["scope_id"], row["entry_key"])
