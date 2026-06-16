"""Mode — execution mode of a node (agent/router/tasker/tool/worker)."""
from __future__ import annotations

from enum import StrEnum


class Mode(StrEnum):
    """Execution mode of a node."""

    AGENT = "agent"
    ROUTER = "router"
    TASKER = "tasker"
    TOOL = "tool"
    WORKER = "worker"
