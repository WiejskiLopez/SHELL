"""Rejestracja Command Handlers na CommandBus."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.execution.edge_execution.commands.create_edge_execution_command import (
    CreateEdgeExecutionCommand,
)
from shell.application.execution.edge_execution.commands.delete_edge_execution_command import (
    DeleteEdgeExecutionCommand,
)
from shell.application.execution.edge_execution.commands.update_edge_execution_command import (
    UpdateEdgeExecutionCommand,
)
from shell.application.execution.edge_link_execution.commands.create_edge_link_execution_command import (
    CreateEdgeLinkExecutionCommand,
)
from shell.application.execution.edge_link_execution.commands.delete_edge_link_execution_command import (
    DeleteEdgeLinkExecutionCommand,
)
from shell.application.execution.edge_link_execution.commands.update_edge_link_execution_command import (
    UpdateEdgeLinkExecutionCommand,
)
from shell.application.execution.node_execution.commands.create_node_execution_command import (
    CreateNodeExecutionCommand,
)
from shell.application.execution.node_execution.commands.delete_node_execution_command import (
    DeleteNodeExecutionCommand,
)
from shell.application.execution.session_execution.commands.close_session_command import (
    CloseSessionCommand,
)
from shell.application.execution.session_execution.commands.open_session_command import (
    OpenSessionCommand,
)
from shell.application.execution.workflow.commands.create_workflow_command import (
    CreateWorkflowCommand,
)
from shell.application.execution.workflow.commands.delete_workflow_command import (
    DeleteWorkflowCommand,
)
from shell.application.execution.workflow.commands.update_workflow_command import (
    UpdateWorkflowCommand,
)
from shell.application.messaging.message_router.commands.create_message_router_command import (
    CreateMessageRouterCommand,
)
from shell.application.messaging.message_router.commands.delete_message_router_command import (
    DeleteMessageRouterCommand,
)
from shell.application.messaging.message_router.commands.update_message_router_command import (
    UpdateMessageRouterCommand,
)
from shell.application.project.project.commands.create_project_command import (
    CreateProjectCommand,
)
from shell.application.project.project.commands.delete_project_command import (
    DeleteProjectCommand,
)
from shell.application.project.project.commands.update_project_command import (
    UpdateProjectCommand,
)
from shell.application.scheduling.scheduler_definition.commands.create_scheduler_definition_command import (
    CreateSchedulerDefinitionCommand,
)
from shell.application.scheduling.scheduler_definition.commands.delete_scheduler_definition_command import (
    DeleteSchedulerDefinitionCommand,
)
from shell.application.scheduling.scheduler_definition.commands.update_scheduler_definition_command import (
    UpdateSchedulerDefinitionCommand,
)
from shell.application.scheduling.scheduler_execution.commands.create_scheduler_execution_command import (
    CreateSchedulerExecutionCommand,
)
from shell.application.scheduling.scheduler_execution.commands.delete_scheduler_execution_command import (
    DeleteSchedulerExecutionCommand,
)
from shell.application.scheduling.scheduler_execution.commands.update_scheduler_execution_command import (
    UpdateSchedulerExecutionCommand,
)
from shell.application.scheduling.scheduler_job.commands.create_scheduler_job_command import (
    CreateSchedulerJobCommand,
)
from shell.application.scheduling.scheduler_job.commands.delete_scheduler_job_command import (
    DeleteSchedulerJobCommand,
)
from shell.application.scheduling.scheduler_job.commands.update_scheduler_job_command import (
    UpdateSchedulerJobCommand,
)
from shell.application.session.session.commands.delete_session_command import (
    DeleteSessionCommand,
)
from shell.application.session.session.commands.update_session_command import (
    UpdateSessionCommand,
)
from shell.application.user.user.commands.create_user_command import CreateUserCommand
from shell.application.user.user.commands.delete_user_command import DeleteUserCommand
from shell.application.user.user.commands.update_user_command import UpdateUserCommand

if TYPE_CHECKING:
    from shell.platform.bootstrap.container.core_container import Container


def register_commands(container: Container) -> None:
    """Rejestruje wszystkie Command Handlers na CommandBus kontenera."""

    cmd_bus = container.app.buses.command_bus
    commands = container.app.commands

    cmd_bus.register(
        CreateNodeExecutionCommand,
        commands.create_node_execution_handler_factory,
    )
    cmd_bus.register(
        DeleteNodeExecutionCommand,
        commands.delete_node_execution_handler_factory,
    )

    cmd_bus.register(
        CreateEdgeExecutionCommand,
        commands.create_edge_execution_handler_factory,
    )
    cmd_bus.register(
        UpdateEdgeExecutionCommand,
        commands.update_edge_execution_handler_factory,
    )
    cmd_bus.register(
        DeleteEdgeExecutionCommand,
        commands.delete_edge_execution_handler_factory,
    )

    cmd_bus.register(
        CreateEdgeLinkExecutionCommand,
        commands.create_edge_link_execution_handler_factory,
    )
    cmd_bus.register(
        DeleteEdgeLinkExecutionCommand,
        commands.delete_edge_link_execution_handler_factory,
    )
    cmd_bus.register(
        UpdateEdgeLinkExecutionCommand,
        commands.update_edge_link_execution_handler_factory,
    )

    cmd_bus.register(CreateUserCommand, commands.create_user_handler_factory)
    cmd_bus.register(UpdateUserCommand, commands.update_user_handler_factory)
    cmd_bus.register(DeleteUserCommand, commands.delete_user_handler_factory)

    cmd_bus.register(OpenSessionCommand, commands.open_session_handler_factory)
    cmd_bus.register(CloseSessionCommand, commands.close_session_handler_factory)
    cmd_bus.register(UpdateSessionCommand, commands.update_session_handler_factory)
    cmd_bus.register(DeleteSessionCommand, commands.delete_session_handler_factory)

    cmd_bus.register(CreateMessageRouterCommand, commands.create_message_router_handler_factory)
    cmd_bus.register(UpdateMessageRouterCommand, commands.update_message_router_handler_factory)
    cmd_bus.register(DeleteMessageRouterCommand, commands.delete_message_router_handler_factory)

    cmd_bus.register(
        CreateSchedulerDefinitionCommand, commands.create_scheduler_definition_handler_factory
    )
    cmd_bus.register(
        UpdateSchedulerDefinitionCommand, commands.update_scheduler_definition_handler_factory
    )
    cmd_bus.register(
        DeleteSchedulerDefinitionCommand, commands.delete_scheduler_definition_handler_factory
    )

    cmd_bus.register(
        CreateSchedulerExecutionCommand, commands.create_scheduler_execution_handler_factory
    )
    cmd_bus.register(
        UpdateSchedulerExecutionCommand, commands.update_scheduler_execution_handler_factory
    )
    cmd_bus.register(
        DeleteSchedulerExecutionCommand, commands.delete_scheduler_execution_handler_factory
    )

    cmd_bus.register(CreateSchedulerJobCommand, commands.create_scheduler_job_handler_factory)
    cmd_bus.register(UpdateSchedulerJobCommand, commands.update_scheduler_job_handler_factory)
    cmd_bus.register(DeleteSchedulerJobCommand, commands.delete_scheduler_job_handler_factory)

    cmd_bus.register(CreateProjectCommand, commands.create_project_handler_factory)
    cmd_bus.register(UpdateProjectCommand, commands.update_project_handler_factory)
    cmd_bus.register(DeleteProjectCommand, commands.delete_project_handler_factory)

    cmd_bus.register(CreateWorkflowCommand, commands.create_workflow_handler_factory)
    cmd_bus.register(UpdateWorkflowCommand, commands.update_workflow_handler_factory)
    cmd_bus.register(DeleteWorkflowCommand, commands.delete_workflow_handler_factory)
