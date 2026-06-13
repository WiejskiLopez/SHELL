"""NodeExecutionPolicy — decides what to do after a single node finishes.

The policy abstracts the failure handling rule for a workflow:
- ``FailFastPolicy`` (default) aborts the workflow on first failure.
- Future policies (``ContinueOnFailurePolicy``, ``RetryWithBackoffPolicy``,
  etc.) plug in here without touching the worker.

A policy is a pure domain service (no I/O, no async).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell_ddd.domain.entities.workflow import Workflow
    from shell_ddd.domain.value_objects.ids import NodeId


class PolicyAction:
    """Marker base class for policy decisions."""


@dataclass(frozen=True, slots=True)
class AbortDecision(PolicyAction):
    """Signal: stop the workflow and mark it as failed."""

    reason: str = ""


@dataclass(frozen=True, slots=True)
class ContinueDecision(PolicyAction):
    """Signal: continue with the next node despite the failure."""


PolicyDecision = AbortDecision | ContinueDecision


class NodeExecutionPolicy(Protocol):
    """Decides what to do after a node has failed."""

    def decide_after_failure(
        self,
        workflow: "Workflow",
        failed_node_id: "NodeId",
        reason: str,
    ) -> PolicyDecision:
        """Return AbortDecision or ContinueDecision."""
        ...


class FailFastPolicy:
    """Default policy — stop the workflow immediately on the first failure."""

    def decide_after_failure(
        self,
        workflow: "Workflow",
        failed_node_id: "NodeId",
        reason: str,
    ) -> PolicyDecision:
        return AbortDecision(reason=reason)
