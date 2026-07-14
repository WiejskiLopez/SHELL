from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection

from shell.infrastructure.definition.graph_definition.persistence.sql.models import (
    GraphDefinitionModel,
)
from shell.infrastructure.definition.node_definition.persistence.sql.models import (
    NodeDefinitionModel,
)
from shell.infrastructure.definition.node_link_definition.persistence.sql.models import (
    NodeLinkDefinitionModel,
)
from shell.platform.infrastructure.persistence.sql import reset_database, run_migrations


async def bootstrap_definition_database(url: str, reset_db: bool = False) -> None:
    if reset_db:
        await reset_database(url)
    await run_migrations(url)
    await _seed_base_definition_data(url)


def _seed_sync(sync_conn: Connection) -> None:
    session = Session(sync_conn)

    graph_definition_model = session.execute(
        select(GraphDefinitionModel).where(GraphDefinitionModel.id == "base-planner-id")
    ).scalar_one_or_none()

    if graph_definition_model is None:
        graph_definition_model = GraphDefinitionModel(
            id="base-planner-id",
        )
        session.add(graph_definition_model)
        session.flush()

    link = session.execute(
        select(NodeLinkDefinitionModel).where(
            NodeLinkDefinitionModel.graph_definition_id == graph_definition_model.id
        )
    ).scalar_one_or_none()

    if link is None:
        node = NodeDefinitionModel(
            id="base-planner-node-1",
            node_type="agent",
        )
        session.add(node)
        session.flush()

        link = NodeLinkDefinitionModel(
            id="base-planner-link-1",
            graph_definition_id=graph_definition_model.id,
            node_definition_id=node.id,
        )
        session.add(link)

    session.commit()


async def _seed_base_definition_data(url: str) -> None:
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(url, echo=False, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(_seed_sync)
    await engine.dispose()
