"""Fresh baseline schema for the Definition bounded context."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine

from shell.definition.infrastructure.definition.graph_definition.persistence.sql.models.graph_definition import (
    GraphDefinitionModel,
)
from shell.definition.infrastructure.definition.graph_definition_embedding.persistence.sql.models.graph_definition_embedding import (
    GraphDefinitionEmbeddingModel,
)
from shell.definition.infrastructure.definition.node_definition.persistence.sql.models.node_definition import (
    NodeDefinitionModel,
)
from shell.definition.infrastructure.definition.node_link_definition.persistence.sql.models.node_link_definition import (
    NodeLinkDefinitionModel,
)
from shell.definition.infrastructure.definition.runner_config.persistence.sql.models.runner_config import (
    RunnerConfigModel,
)
from shell.platform.infrastructure.persistence.sql.models.audit_event import AuditEventModel
from shell.platform.infrastructure.persistence.sql.models.base import Base
from shell.platform.infrastructure.persistence.sql.models.event.inbox_event import InboxEventModel
from shell.platform.infrastructure.persistence.sql.models.event.outbox_event import OutboxEventModel

_TABLES = (
    GraphDefinitionModel.__table__,
    GraphDefinitionEmbeddingModel.__table__,
    NodeDefinitionModel.__table__,
    NodeLinkDefinitionModel.__table__,
    RunnerConfigModel.__table__,
    AuditEventModel.__table__,
    OutboxEventModel.__table__,
    InboxEventModel.__table__,
)


async def run_definition_baseline(url: str) -> None:
    engine = create_async_engine(
        url,
        future=True,
        connect_args={"check_same_thread": False} if "sqlite" in url else {},
    )
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=list(_TABLES))
    await engine.dispose()
