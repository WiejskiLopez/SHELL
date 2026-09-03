"""Stable wire contracts for Project bounded-context delivery commands."""

from __future__ import annotations

from shell.platform.application.contracts.command_contract import CommandContract
from shell.platform.infrastructure.serialization.registries.command_registry import (
    build_command_registry,
    discover_command_types,
)
from shell.project_service.application.project.project_provision.commands.provision_workspace_command import (
    ProvisionWorkspaceCommand,
)
from shell.project_service.application.project.project_provision.commands.release_workspace_command import (
    ReleaseWorkspaceCommand,
)
from shell.project_service.application.project.project_provision.commands.start_project_provision_command import (
    StartProjectProvisionCommand,
)

PROJECT_COMMAND_CONTRACTS: dict[str, CommandContract] = {
    "project.project_provision.start": CommandContract(
        command_name="project.project_provision.start",
        command_class=StartProjectProvisionCommand,
        target_service="project",
    ),
    "project.project_provision.provision_workspace": CommandContract(
        command_name="project.project_provision.provision_workspace",
        command_class=ProvisionWorkspaceCommand,
        target_service="project",
    ),
    "project.project_provision.release_workspace": CommandContract(
        command_name="project.project_provision.release_workspace",
        command_class=ReleaseWorkspaceCommand,
        target_service="project",
    ),
}


def build_project_command_registry() -> dict[str, type]:
    """Build the local command registry and add stable delivery names."""
    registry = build_command_registry(
        discover_command_types("shell.project_service.application.project")
    )
    registry.update(
        {
            contract.command_name: contract.command_class
            for contract in PROJECT_COMMAND_CONTRACTS.values()
        }
    )
    return registry