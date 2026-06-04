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


def _db_makedirs(port: DbNodePort, path: PathType) -> None:
    scope_id = _resolve_dir_scope(port, path)
    port.memory_.put_entry(CONTEXT_TYPE_NODE_FILE, scope_id, DIR_MARKER_KEY, {"is_dir": True})
