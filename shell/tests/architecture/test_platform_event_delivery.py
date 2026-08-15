"""Architecture tests for per-BC platform event delivery models."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from shell.platform.infrastructure.persistence.sql.models.event_delivery import (
    build_event_delivery_models,
)


def test_event_delivery_models_are_bound_to_the_consuming_bc_metadata() -> None:
    class DefinitionBase(DeclarativeBase):
        metadata = MetaData()

    class ExecutionBase(DeclarativeBase):
        metadata = MetaData()

    definition_models = build_event_delivery_models(DefinitionBase)
    execution_models = build_event_delivery_models(ExecutionBase)

    assert definition_models.outbox.metadata is DefinitionBase.metadata
    assert definition_models.inbox.metadata is DefinitionBase.metadata
    assert execution_models.outbox.metadata is ExecutionBase.metadata
    assert execution_models.inbox.metadata is ExecutionBase.metadata
    assert definition_models.outbox is not execution_models.outbox
    assert set(DefinitionBase.metadata.tables) == {"inbox_event", "outbox_event"}
    assert set(ExecutionBase.metadata.tables) == {"inbox_event", "outbox_event"}
