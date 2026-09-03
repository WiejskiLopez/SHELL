from __future__ import annotations

from shell.platform.process.saga.saga_timed_out import SagaTimedOut
from shell.project_service.application.project.project_provision.commands.provision_workspace_command import (
    ProvisionWorkspaceCommand,
)
from shell.project_service.application.project.project_provision.commands.release_workspace_command import (
    ReleaseWorkspaceCommand,
)
from shell.project_service.application.project.project_provision.commands.start_project_provision_command import (
    StartProjectProvisionCommand,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_provision_failed_integration_event import (
    WorkspaceProvisionFailedIntegrationEvent,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_provisioned_integration_event import (
    WorkspaceProvisionedIntegrationEvent,
)
from shell.project_service.application.project.project_provision.integration_events.workspace_released_integration_event import (
    WorkspaceReleasedIntegrationEvent,
)
from shell.project_service.bootstrap.project.command_contracts import PROJECT_COMMAND_CONTRACTS
from shell.project_service.bootstrap.project.container.project_core_container import (
    ProjectCoreContainer,
    configure_project_container,
)


def test_project_container_registers_saga_roles() -> None:
    container = ProjectCoreContainer()

    configure_project_container(container)

    command_handlers = container.command_bus()._handler_factories
    assert StartProjectProvisionCommand in command_handlers
    assert ProvisionWorkspaceCommand in command_handlers
    assert ReleaseWorkspaceCommand in command_handlers

    event_handlers = container.event_bus()._handler_factories
    assert WorkspaceProvisionedIntegrationEvent in event_handlers
    assert WorkspaceProvisionFailedIntegrationEvent in event_handlers
    assert WorkspaceReleasedIntegrationEvent in event_handlers
    assert SagaTimedOut in event_handlers

    assert set(PROJECT_COMMAND_CONTRACTS) == {
        "project.project_provision.start",
        "project.project_provision.provision_workspace",
        "project.project_provision.release_workspace",
    }