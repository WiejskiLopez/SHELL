from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import registry

from shell.platform.infrastructure.persistence.sql.models.base import SqlAlchemyModelBase
from shell.platform.infrastructure.persistence.sql.models.persistence_delivery import (
    build_persistence_delivery_models,
)


class ProjectSqlAlchemyModelBase(SqlAlchemyModelBase):
    __abstract__ = True
    metadata = MetaData()
    registry = registry()


PERSISTENCE_DELIVERY_MODELS = build_persistence_delivery_models(ProjectSqlAlchemyModelBase)
EVENT_DELIVERY_MODELS = PERSISTENCE_DELIVERY_MODELS.events
COMMAND_DELIVERY_MODELS = PERSISTENCE_DELIVERY_MODELS.commands
InboxEventModel = EVENT_DELIVERY_MODELS.inbox
OutboxEventModel = EVENT_DELIVERY_MODELS.outbox
