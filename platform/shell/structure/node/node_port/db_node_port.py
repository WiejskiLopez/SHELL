"""db_node_port.py
DbNodePort — adapter NodePort over Memory (SqlMemoryBackend context_entry).

Slots:
    _memory      — Memory facade (None until init)
    _node_dir    — root path of the node; all paths are resolved relative to it
    _node_name   — symbolic name of the node (used in scope_id)
    _workflow_id — Optional; workflow_id used as scope_id prefix; '_global' if None
"""

from __future__ import annotations

from shell.memory.memory.memory import Memory
from shell.structure.node.node_port.internal._assert_db_node_port_set import _assert_db_node_port_set
from shell.structure.node.node_port.internal._db_exists import _db_exists
from shell.structure.node.node_port.internal._db_list_files import _db_list_files
from shell.structure.node.node_port.internal._db_makedirs import _db_makedirs
from shell.structure.node.node_port.internal._db_move import _db_move
from shell.structure.node.node_port.internal._db_read_text import _db_read_text
from shell.structure.node.node_port.internal._db_rmtree import _db_rmtree
from shell.structure.node.node_port.internal._db_unlink import _db_unlink
from shell.structure.node.node_port.internal._db_write_text import _db_write_text
from shell.structure.node.node_port.internal._init_db_node_port import _init_db_node_port
from shell.structure.node.node_port.node_port import NodePort
from shell.utils.path.path import PathType


class DbNodePort:
    """NodePort implementation backed by Memory (context_entry table).

    Maps every absolute filesystem path under node_dir into a (scope_id, entry_key)
    pair persisted in context_entry of context_type 'node_file'.
    """

    __slots__ = ("_memory", "_node_dir", "_node_name", "_workflow_id")

    def __init__(self) -> None:
        self._memory: Memory | None = None
        self._node_dir: PathType | None = None
        self._node_name: str | None = None
        self._workflow_id: str | None = None

    @property
    def memory_(self) -> Memory:
        _assert_db_node_port_set(self._memory, "memory")
        return self._memory

    @property
    def node_dir_(self) -> PathType:
        _assert_db_node_port_set(self._node_dir, "node_dir")
        return self._node_dir

    @property
    def node_name_(self) -> str:
        _assert_db_node_port_set(self._node_name, "node_name")
        return self._node_name

    @property
    def workflow_id_(self) -> str | None:
        return self._workflow_id

    def set_workflow_id(self, workflow_id: str | None) -> None:
        self._workflow_id = workflow_id

    def init_db_node_port(self, memory: Memory, node_dir: PathType, node_name: str, workflow_id: str | None = None) -> None:
        _init_db_node_port(self, memory, node_dir, node_name, workflow_id)

    def makedirs(self, path: PathType) -> None:
        _db_makedirs(self, path)

    def exists(self, path: PathType) -> bool:
        return _db_exists(self, path)

    def rmtree(self, path: PathType) -> None:
        _db_rmtree(self, path)

    def read_text(self, path: PathType) -> str:
        return _db_read_text(self, path)

    def write_text(self, path: PathType, content: str) -> None:
        _db_write_text(self, path, content)

    def unlink(self, path: PathType) -> None:
        _db_unlink(self, path)

    def list_files(self, path: PathType, suffix: str = "") -> list[PathType]:
        return _db_list_files(self, path, suffix)

    def move(self, src: PathType, dst: PathType) -> None:
        _db_move(self, src, dst)


_: NodePort = DbNodePort()
