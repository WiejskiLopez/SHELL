from __future__ import annotations

_MODES_REQUIRING_NODE_DIR = frozenset({'agent', 'tasker', 'router', 'tool', 'worker'})


def _assert_node_dir_set(node_dir: str | None, mode: str | None) -> None:
    if mode in _MODES_REQUIRING_NODE_DIR and node_dir is None:
        raise ValueError(f"[Cli] --node-dir is required in {mode} mode")
