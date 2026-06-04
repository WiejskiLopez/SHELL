from __future__ import annotations

from typing import TYPE_CHECKING

from shell.memory.memory.memory import Memory
from shell.utils.path.path import PathType

if TYPE_CHECKING:
    from shell.structure.node.node_port.db_node_port import DbNodePort


def _init_db_node_port(port: DbNodePort, memory: Memory, node_dir: PathType, node_name: str, workflow_id: str | None = None) -> None:
    port._memory = memory
    port._node_dir = node_dir
    port._node_name = node_name
    port._workflow_id = workflow_id
