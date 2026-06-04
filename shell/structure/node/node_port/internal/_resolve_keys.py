"""_resolve_keys.py
Map an absolute path under node_dir to (scope_id, entry_key) used in context_entry.

Convention:
    scope_id = '<workflow_id>:<node_name>:<rel_dir>'
    workflow_id falls back to '_global' when not set on the port.

    For a FILE path /node_dir/.node/input/foo.yaml on node 'agent-1' in workflow 'wf-1':
        scope_id  = 'wf-1:agent-1:.node/input'
        entry_key = 'foo.yaml'

    For a DIR path /node_dir/.node/input on node 'agent-1' in workflow 'wf-1':
        scope_id  = 'wf-1:agent-1:.node/input'
        entry_key = ''   (caller decides how to use; usually marker '.dir')

The path must be relative to (or equal to) node_dir; absolute paths outside are rejected.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.utils.path.path import PathType

if TYPE_CHECKING:
    from shell.structure.node.node_port.db_node_port import DbNodePort


CONTEXT_TYPE_NODE_FILE = "node_file"
DIR_MARKER_KEY = ".dir"


def _resolve_relative(port: DbNodePort, path: PathType) -> str:
    node_dir = port.node_dir_
    try:
        rel = Path.resolve(path).relative_to(Path.resolve(node_dir))
    except ValueError as exc:
        raise ValueError(f"DbNodePort: path {path} is not under node_dir {node_dir}") from exc
    return rel.as_posix()


def _workflow_prefix(port: DbNodePort) -> str:
    return port.workflow_id_ if port.workflow_id_ else "_global"


def _resolve_file_keys(port: DbNodePort, path: PathType) -> tuple[str, str]:
    rel_str = _resolve_relative(port, path)
    if rel_str in ("", "."):
        raise ValueError(f"DbNodePort: cannot use node_dir itself as a file path ({path})")
    parent, _, name = rel_str.rpartition("/")
    wf = _workflow_prefix(port)
    scope_id = f"{wf}:{port.node_name_}:{parent}" if parent else f"{wf}:{port.node_name_}:"
    return scope_id, name


def _resolve_dir_scope(port: DbNodePort, path: PathType) -> str:
    rel_str = _resolve_relative(port, path)
    wf = _workflow_prefix(port)
    return f"{wf}:{port.node_name_}:{rel_str}" if rel_str not in ("", ".") else f"{wf}:{port.node_name_}:"
