from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class NodeExecutionDeletedIntegrationEvent(IntegrationEvent):
    node_execution_id: str
