"""Command wire contract — explicit, stable identity of an asynchronous command."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from shell.platform.application.commands.command import Command


@dataclass(frozen=True, slots=True)
class CommandContract:
    """Stable wire identity of a command; independent of the Python class name."""

    command_name: str
    command_class: type[Command]
    target_service: str
    schema_version: int = 1


def command_contracts_by_class(
    contracts: Mapping[str, CommandContract],
) -> dict[type, CommandContract]:
    """Index contracts by command class for O(1) lookup during dispatch."""
    return {contract.command_class: contract for contract in contracts.values()}