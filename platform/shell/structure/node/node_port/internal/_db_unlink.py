from __future__ import annotations

from typing import TYPE_CHECKING

from shell.structure.node.node_port.internal._resolve_keys import (
    CONTEXT_TYPE_NODE_FILE,
    _resolve_file_keys,
)
from shell.utils.path.path import PathType

if TYPE_CHECKING:
    from shell.structure.node.node_port.db_node_port import DbNodePort


def _db_unlink(port: DbNodePort, path: PathType) -> None:
    scope_id, entry_key = _resolve_file_keys(port, path)
    port.memory_.delete_entry(CONTEXT_TYPE_NODE_FILE, scope_id, entry_key)
