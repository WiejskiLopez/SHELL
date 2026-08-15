"""Architecture tests for per-BC message and command delivery models."""

from __future__ import annotations

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

from shell.platform.infrastructure.persistence.sql.models.command_delivery import (
    build_command_delivery_models,
)
from shell.platform.infrastructure.persistence.sql.models.message_delivery import (
    build_message_delivery_models,
)


def test_message_and_command_models_are_bound_to_consuming_bc_metadata() -> None:
    class DefinitionBase(DeclarativeBase):
        metadata = MetaData()

    class ExecutionBase(DeclarativeBase):
        metadata = MetaData()

    definition_messages = build_message_delivery_models(DefinitionBase)
    execution_messages = build_message_delivery_models(ExecutionBase)
    definition_commands = build_command_delivery_models(DefinitionBase)
    execution_commands = build_command_delivery_models(ExecutionBase)

    assert definition_messages.outbox.metadata is DefinitionBase.metadata
    assert definition_messages.inbox.metadata is DefinitionBase.metadata
    assert execution_messages.outbox.metadata is ExecutionBase.metadata
    assert execution_messages.inbox.metadata is ExecutionBase.metadata
    assert definition_commands.outbox.metadata is DefinitionBase.metadata
    assert definition_commands.inbox.metadata is DefinitionBase.metadata
    assert execution_commands.outbox.metadata is ExecutionBase.metadata
    assert execution_commands.inbox.metadata is ExecutionBase.metadata

    assert definition_messages.outbox is not execution_messages.outbox
    assert definition_commands.inbox is not execution_commands.inbox
    assert set(DefinitionBase.metadata.tables) == {
        "inbox_command",
        "inbox_message",
        "outbox_command",
        "outbox_message",
    }
    assert set(ExecutionBase.metadata.tables) == set(DefinitionBase.metadata.tables)
