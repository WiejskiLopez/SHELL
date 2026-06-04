from __future__ import annotations

from typing import TYPE_CHECKING

from shell.structure.node.node_port.internal._db_read_text import _db_read_text
from shell.structure.node.node_port.internal._db_unlink import _db_unlink
from shell.structure.node.node_port.internal._db_write_text import _db_write_text
from shell.utils.path.path import PathType

if TYPE_CHECKING:
    from shell.structure.node.node_port.db_node_port import DbNodePort


def _db_move(port: DbNodePort, src: PathType, dst: PathType) -> None:
    body = _db_read_text(port, src)
    _db_write_text(port, dst, body)
    _db_unlink(port, src)
