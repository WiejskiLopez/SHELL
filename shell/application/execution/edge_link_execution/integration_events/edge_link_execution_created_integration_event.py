from __future__ import annotations

from dataclasses import dataclass

from shell.platform.application.events import IntegrationEvent


@dataclass(frozen=True, slots=True)
class EdgeLinkExecutionCreatedIntegrationEvent(IntegrationEvent):
    edge_link_execution_id: str
    node_execution_id: str
    edge_execution_id: str
