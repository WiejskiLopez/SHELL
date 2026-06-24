"""Mode — execution mode of a node.

.. deprecated::
   Use NodeRole from shell.domain.execution.value_objects.node_role for new code.
"""

from __future__ import annotations

from enum import StrEnum

from shell.domain.platform.base.value_object import ValueObject


class Mode(ValueObject, StrEnum):
    """Execution mode of a graph_node."""

    AGENT = "agent"
    ROUTER = "router"
    TASKER = "tasker"
    TOOL = "tool"
    WORKER = "worker"
    PLANNER = "planner"
    VERIFIER = "verifier"
