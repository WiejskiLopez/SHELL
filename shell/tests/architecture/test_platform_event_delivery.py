"""Koncept: reguła architektoniczna dotycząca platform event delivery.

Reguła: test sprawdza kontrakt architektoniczny platform event delivery.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import architecture_assertion_message
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
    assert definition_models.outbox.metadata is DefinitionBase.metadata, (
        architecture_assertion_message(
            "reguła testowana przez test_event_delivery_models_are_bound_to_the_consuming_bc_metadata",
            "warunek zapisany w asercji musi być spełniony",
            "Asercja nie zawierała dodatkowych szczegółów.",
        )
    )
    assert definition_models.inbox.metadata is DefinitionBase.metadata, (
        architecture_assertion_message(
            "reguła testowana przez test_event_delivery_models_are_bound_to_the_consuming_bc_metadata",
            "warunek zapisany w asercji musi być spełniony",
            "Asercja nie zawierała dodatkowych szczegółów.",
        )
    )
    assert execution_models.outbox.metadata is ExecutionBase.metadata, (
        architecture_assertion_message(
            "reguła testowana przez test_event_delivery_models_are_bound_to_the_consuming_bc_metadata",
            "warunek zapisany w asercji musi być spełniony",
            "Asercja nie zawierała dodatkowych szczegółów.",
        )
    )
    assert execution_models.inbox.metadata is ExecutionBase.metadata, (
        architecture_assertion_message(
            "reguła testowana przez test_event_delivery_models_are_bound_to_the_consuming_bc_metadata",
            "warunek zapisany w asercji musi być spełniony",
            "Asercja nie zawierała dodatkowych szczegółów.",
        )
    )
    assert definition_models.outbox is not execution_models.outbox, architecture_assertion_message(
        "reguła testowana przez test_event_delivery_models_are_bound_to_the_consuming_bc_metadata",
        "warunek zapisany w asercji musi być spełniony",
        "Asercja nie zawierała dodatkowych szczegółów.",
    )
    assert set(DefinitionBase.metadata.tables) == {"inbox_event", "outbox_event"}, (
        architecture_assertion_message(
            "reguła testowana przez test_event_delivery_models_are_bound_to_the_consuming_bc_metadata",
            "warunek zapisany w asercji musi być spełniony",
            "Asercja nie zawierała dodatkowych szczegółów.",
        )
    )
    assert set(ExecutionBase.metadata.tables) == {"inbox_event", "outbox_event"}, (
        architecture_assertion_message(
            "reguła testowana przez test_event_delivery_models_are_bound_to_the_consuming_bc_metadata",
            "warunek zapisany w asercji musi być spełniony",
            "Asercja nie zawierała dodatkowych szczegółów.",
        )
    )
