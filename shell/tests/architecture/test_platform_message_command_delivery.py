"""Koncept: reguła architektoniczna dotycząca platform message command delivery.

Reguła: test sprawdza kontrakt architektoniczny platform message command delivery.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

from _arch_helpers import architecture_assertion_message
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
    assert definition_messages.outbox.metadata is DefinitionBase.metadata, architecture_assertion_message('reguła testowana przez test_message_and_command_models_are_bound_to_consuming_bc_metadata', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
    assert definition_messages.inbox.metadata is DefinitionBase.metadata, architecture_assertion_message('reguła testowana przez test_message_and_command_models_are_bound_to_consuming_bc_metadata', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
    assert execution_messages.outbox.metadata is ExecutionBase.metadata, architecture_assertion_message('reguła testowana przez test_message_and_command_models_are_bound_to_consuming_bc_metadata', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
    assert execution_messages.inbox.metadata is ExecutionBase.metadata, architecture_assertion_message('reguła testowana przez test_message_and_command_models_are_bound_to_consuming_bc_metadata', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
    assert definition_commands.outbox.metadata is DefinitionBase.metadata, architecture_assertion_message('reguła testowana przez test_message_and_command_models_are_bound_to_consuming_bc_metadata', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
    assert definition_commands.inbox.metadata is DefinitionBase.metadata, architecture_assertion_message('reguła testowana przez test_message_and_command_models_are_bound_to_consuming_bc_metadata', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
    assert execution_commands.outbox.metadata is ExecutionBase.metadata, architecture_assertion_message('reguła testowana przez test_message_and_command_models_are_bound_to_consuming_bc_metadata', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
    assert execution_commands.inbox.metadata is ExecutionBase.metadata, architecture_assertion_message('reguła testowana przez test_message_and_command_models_are_bound_to_consuming_bc_metadata', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
    assert definition_messages.outbox is not execution_messages.outbox, architecture_assertion_message('reguła testowana przez test_message_and_command_models_are_bound_to_consuming_bc_metadata', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
    assert definition_commands.inbox is not execution_commands.inbox, architecture_assertion_message('reguła testowana przez test_message_and_command_models_are_bound_to_consuming_bc_metadata', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
    assert set(DefinitionBase.metadata.tables) == {'inbox_command', 'inbox_message', 'outbox_command', 'outbox_message'}, architecture_assertion_message('reguła testowana przez test_message_and_command_models_are_bound_to_consuming_bc_metadata', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
    assert set(ExecutionBase.metadata.tables) == set(DefinitionBase.metadata.tables), architecture_assertion_message('reguła testowana przez test_message_and_command_models_are_bound_to_consuming_bc_metadata', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
