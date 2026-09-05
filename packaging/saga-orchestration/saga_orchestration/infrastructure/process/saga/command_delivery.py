"""Command delivery adapter used by saga process managers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.infrastructure.messaging.command.sql_command_outbox_writer import (
    SqlCommandDeliveryDispatcher,
    SqlCommandOutboxWriter,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from saga_orchestration.process.saga.ports.command_delivery_dispatcher import (
        CommandDeliveryDispatcher,
    )
    from shell.platform.application.contracts.command_contract import CommandContract
    from shell.platform.infrastructure.persistence.sql.models.command_delivery import (
        CommandDeliveryModels,
    )


def build_command_delivery_dispatcher(
    *,
    commands: Mapping[str, CommandContract],
    models: CommandDeliveryModels,
    source_service: str,
) -> CommandDeliveryDispatcher:
    writer = SqlCommandOutboxWriter(models=models, source_service=source_service)
    return SqlCommandDeliveryDispatcher(commands=commands, writer=writer)
