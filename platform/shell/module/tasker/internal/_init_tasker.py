from __future__ import annotations

from shell.module.tasker.internal._validate_task import _validate_task
from shell.module.tasker.internal._seed_graph_node_task import _seed_graph_node_task


def _init_tasker(tasker, reader=None) -> None:
    _validate_task(tasker._app)
    tasker.graph_.init_graph()
    _seed_graph_node_task(tasker)
