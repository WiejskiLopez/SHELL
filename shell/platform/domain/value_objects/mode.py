"""Mode — execution mode of a node.

Mode and NodeRole are different concepts with different semantics.
Mode represents the execution mode (agent, router, tasker, etc.)
while NodeRole represents the role in a workflow graph.
"""

from __future__ import annotations

from enum import StrEnum

from shell.platform.domain.base.value_object import ValueObject


class Mode(ValueObject, StrEnum):
    """Execution mode of a node."""

    AGENT = "agent"
    ROUTER = "router"
    TASKER = "tasker"
    TOOL = "tool"
    WORKER = "worker"
    PLANNER = "planner"
    VERIFIER = "verifier"
