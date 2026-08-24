"""Platform-owned SQL delivery models for integration tests."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from shell.platform.infrastructure.persistence.sql.models.persistence_delivery import (
    PersistenceDeliveryModels,
    build_persistence_delivery_models,
)


class PlatformTestModelBase(DeclarativeBase):
    metadata = MetaData()


PERSISTENCE_DELIVERY_MODELS: PersistenceDeliveryModels = build_persistence_delivery_models(
    PlatformTestModelBase
)
EVENT_DELIVERY_MODELS = PERSISTENCE_DELIVERY_MODELS.events
COMMAND_DELIVERY_MODELS = PERSISTENCE_DELIVERY_MODELS.commands
