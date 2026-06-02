from __future__ import annotations

from typing import TYPE_CHECKING

from shell.structure.node.node_port.internal._resolve_keys import (
    CONTEXT_TYPE_NODE_FILE,
    _resolve_dir_scope,
    _resolve_file_keys,
)
from shell.utils.path.path import PathType

if TYPE_CHECKING:
    from shell.structure.node.node_port.db_node_port import DbNodePort


def _db_exists(port: DbNodePort, path: PathType) -> bool:
    scope_id, entry_key = _resolve_file_keys(port, path)
    if port.memory_.get_entry(CONTEXT_TYPE_NODE_FILE, scope_id, entry_key) is not None:
        return True
    dir_scope = _resolve_dir_scope(port, path)
    return len(port.memory_.list_entries(CONTEXT_TYPE_NODE_FILE, dir_scope)) > 0
