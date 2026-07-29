from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class NodeExecutionCreatedIntegrationEvent(IntegrationEvent):
    node_execution_id: str
    node_definition_id: str | None
    graph_execution_id: str | None
