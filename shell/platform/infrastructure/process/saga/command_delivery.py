"""Factory portu ``CommandDeliveryDispatcher`` dla sag (bind kontraktów + writer)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.infrastructure.messaging.command.sql_command_outbox_writer import (
    SqlCommandDeliveryDispatcher,
    SqlCommandOutboxWriter,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from shell.platform.application.contracts.command_contract import CommandContract
    from shell.platform.infrastructure.persistence.sql.models.command_delivery import (
        CommandDeliveryModels,
    )
    from shell.platform.process.saga.ports.command_delivery_dispatcher import (
        CommandDeliveryDispatcher as _Port,
    )


def build_command_delivery_dispatcher(
    *,
    commands: Mapping[str, CommandContract],
    models: CommandDeliveryModels,
    source_service: str,
) -> _Port:
    """Buduje adapter ``CommandDeliveryDispatcher`` na torze ``outbox_command``.

    Dispatch wymaga aktywnego ``DeliverySessionScope`` (transakcja procesora
    inbox); komenda delivery jest zapisywana bez commita — commituje procesor.
    """
    writer = SqlCommandOutboxWriter(models=models, source_service=source_service)
    return SqlCommandDeliveryDispatcher(commands=commands, writer=writer)
