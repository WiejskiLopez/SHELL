from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.value_objects.ids import GraphNodeExecutionId


class _GraphNodeExecutionIdFactory(Protocol):
    """Structural type for a callable that produces a fresh GraphNodeExecutionId."""

    def __call__(self) -> GraphNodeExecutionId: ...
