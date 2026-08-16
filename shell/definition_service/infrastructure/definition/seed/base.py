"""Base/required seed data for the Definition bounded context.

The base planner graph is required for the Definition BC to function:
execution services reference a canonical planner graph by a well-known id.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.definition_service.infrastructure.definition.graph_definition.persistence.sql.models.graph_definition import (
    GraphDefinitionModel,
)
from shell.definition_service.infrastructure.definition.node_link_definition.persistence.sql.models.node_link_definition import (
    NodeLinkDefinitionModel,
)
from shell.definition_service.infrastructure.definition.seed.builders import (
    build_graph_definition_model,
    build_node_definition_model,
    build_node_link_definition_model,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

BASE_PLANNER_GRAPH_ID = "base-planner-id"
BASE_PLANNER_NODE_ID = "base-planner-node-1"
BASE_PLANNER_LINK_ID = "base-planner-link-1"


def seed_base_sync(session: Session) -> None:
    """Insert the canonical base planner graph when missing (idempotent)."""
    graph_definition_model = session.execute(
        select(GraphDefinitionModel).where(GraphDefinitionModel.id == BASE_PLANNER_GRAPH_ID)
    ).scalar_one_or_none()

    if graph_definition_model is None:
        graph_definition_model = build_graph_definition_model(
            graph_definition_id=BASE_PLANNER_GRAPH_ID
        )
        session.add(graph_definition_model)
        session.flush()

    existing_link = session.execute(
        select(NodeLinkDefinitionModel).where(
            NodeLinkDefinitionModel.graph_definition_id == graph_definition_model.id
        )
    ).scalar_one_or_none()

    if existing_link is None:
        node_definition_model = build_node_definition_model(
            node_definition_id=BASE_PLANNER_NODE_ID,
            node_type="agent",
        )
        session.add(node_definition_model)
        session.flush()

        session.add(
            build_node_link_definition_model(
                link_id=BASE_PLANNER_LINK_ID,
                graph_definition_id=graph_definition_model.id,
                node_definition_id=node_definition_model.id,
            )
        )


__all__ = [
    "BASE_PLANNER_GRAPH_ID",
    "seed_base_sync",
]
