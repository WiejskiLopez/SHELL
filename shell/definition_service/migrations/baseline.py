"""Fresh baseline schema for the Definition bounded context."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlalchemy.ext.asyncio import create_async_engine

from shell.definition_service.infrastructure.definition.graph_definition.persistence.sql.models.graph_definition import (
    GraphDefinitionModel,
)
from shell.definition_service.infrastructure.definition.graph_definition_embedding.persistence.sql.models.graph_definition_embedding import (
    GraphDefinitionEmbeddingModel,
)
from shell.definition_service.infrastructure.definition.node_definition.persistence.sql.models.node_definition import (
    NodeDefinitionModel,
)
from shell.definition_service.infrastructure.definition.node_link_definition.persistence.sql.models.node_link_definition import (
    NodeLinkDefinitionModel,
)
from shell.definition_service.infrastructure.definition.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
    DefinitionSqlAlchemyModelBase,
    InboxEventModel,
    OutboxEventModel,
)
from shell.definition_service.infrastructure.definition.runner_config.persistence.sql.models.runner_config import (
    RunnerConfigModel,
)

if TYPE_CHECKING:
    from sqlalchemy import Table

_TABLES: tuple[Table, ...] = cast(
    "tuple[Table, ...]",
    (
        GraphDefinitionModel.__table__,
        GraphDefinitionEmbeddingModel.__table__,
        NodeDefinitionModel.__table__,
        NodeLinkDefinitionModel.__table__,
        RunnerConfigModel.__table__,
        PERSISTENCE_DELIVERY_MODELS.audit.__table__,
        OutboxEventModel.__table__,
        InboxEventModel.__table__,
        PERSISTENCE_DELIVERY_MODELS.messages.outbox.__table__,
        PERSISTENCE_DELIVERY_MODELS.messages.inbox.__table__,
        PERSISTENCE_DELIVERY_MODELS.commands.outbox.__table__,
        PERSISTENCE_DELIVERY_MODELS.commands.inbox.__table__,
        PERSISTENCE_DELIVERY_MODELS.processed_delivery.__table__,
        PERSISTENCE_DELIVERY_MODELS.worker_heartbeat.__table__,
    ),
)


async def run_definition_baseline(url: str, reset_db: bool = False) -> None:
    engine = create_async_engine(
        url,
        future=True,
        connect_args={"check_same_thread": False} if "sqlite" in url else {},
    )
    async with engine.begin() as connection:
        if reset_db:
            await connection.run_sync(
                DefinitionSqlAlchemyModelBase.metadata.drop_all, tables=list(_TABLES)
            )
        await connection.run_sync(
            DefinitionSqlAlchemyModelBase.metadata.create_all, tables=list(_TABLES)
        )
    await engine.dispose()
