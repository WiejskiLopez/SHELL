"""Kontener obsługujący wyłącznie operacje zapisu (Command Handlers)."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.definition.command_handlers.graph_definition_create_handler import (
    GraphDefinitionCreateHandler,
)
from shell.application.definition.command_handlers.runner_config_bootstrap_handler import (
    RunnerConfigBootstrapHandler,
)
from shell.application.execution.command_handlers.edge_execution_create_handler import (
    EdgeExecutionCreateHandler,
)
from shell.application.execution.command_handlers.edge_execution_delete_handler import (
    EdgeExecutionDeleteHandler,
)
from shell.application.execution.command_handlers.edge_execution_update_handler import (
    EdgeExecutionUpdateHandler,
)
from shell.application.execution.command_handlers.edge_link_execution_create_handler import (
    EdgeLinkExecutionCreateHandler,
)
from shell.application.execution.command_handlers.edge_link_execution_delete_handler import (
    EdgeLinkExecutionDeleteHandler,
)
from shell.application.execution.command_handlers.edge_link_execution_update_handler import (
    EdgeLinkExecutionUpdateHandler,
)
from shell.application.execution.command_handlers.node_execution_attach_handler import (
    NodeExecutionAttachHandler,
)
from shell.application.execution.command_handlers.node_execution_create_handler import (
    NodeExecutionCreateHandler,
)
from shell.application.execution.command_handlers.node_execution_run_handler import (
    NodeExecutionRunHandler,
)
from shell.application.execution.command_handlers.node_execution_save_result_handler import (
    NodeExecutionSaveResultHandler,
)
from shell.application.execution.command_handlers.task_execution_import_handler import (
    TaskExecutionImportHandler,
)
from shell.application.execution.command_handlers.workflow_run_tasker_handler import (
    WorkflowRunTaskerHandler,
)
from shell.application.execution.command_handlers.workflow_start_handler import WorkflowStartHandler
from shell.application.user.command_handlers.user_create_handler import UserCreateHandler
from shell.application.user.command_handlers.user_delete_handler import UserDeleteHandler
from shell.application.user.command_handlers.user_update_handler import UserUpdateHandler


class CommandContainer(containers.DeclarativeContainer):
    """Kontener obsługujący wyłącznie operacje zapisu (Command Handlers)."""

    config = providers.Configuration()
    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

    import_task_execution_handler_factory = providers.Factory(
        TaskExecutionImportHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        task_execution_loader=infra.task_execution_loader_factory,
        logger=infra.stdlib_logger,
    )
    start_workflow_handler_factory = providers.Factory(
        WorkflowStartHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
    )
    run_node_execution_handler_factory = providers.Factory(
        NodeExecutionRunHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        workspace=infra.workspace_factory,
        runner=infra.runner_factory,
        strategy=domain.strategy,
    )
    save_node_execution_result_handler_factory = providers.Factory(
        NodeExecutionSaveResultHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
    )
    create_graph_definition_handler_factory = providers.Factory(
        GraphDefinitionCreateHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
    )
    bootstrap_runner_config_handler_factory = providers.Factory(
        RunnerConfigBootstrapHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
    )
    run_tasker_workflow_handler_factory = providers.Factory(
        WorkflowRunTaskerHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        navigator=domain.node_navigator_factory,
    )
    create_node_execution_handler_factory = providers.Factory(
        NodeExecutionCreateHandler,
        unit_of_work=buses.unit_of_work_factory,
        identity=infra.id_generator_factory,
        time=infra.clock_factory,
    )
    attach_node_executions_handler_factory = providers.Factory(
        NodeExecutionAttachHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
    )

    edge_execution_create_handler_factory = providers.Factory(
        EdgeExecutionCreateHandler,
        unit_of_work=buses.unit_of_work_factory,
        identity=infra.id_generator_factory,
        time=infra.clock_factory,
    )
    edge_execution_update_handler_factory = providers.Factory(
        EdgeExecutionUpdateHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
        logger=infra.stdlib_logger,
    )
    edge_execution_delete_handler_factory = providers.Factory(
        EdgeExecutionDeleteHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
        logger=infra.stdlib_logger,
    )

    edge_link_execution_create_handler_factory = providers.Factory(
        EdgeLinkExecutionCreateHandler,
        unit_of_work=buses.unit_of_work_factory,
        identity=infra.id_generator_factory,
        time=infra.clock_factory,
    )
    edge_link_execution_delete_handler_factory = providers.Factory(
        EdgeLinkExecutionDeleteHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
        logger=infra.stdlib_logger,
    )
    edge_link_execution_update_handler_factory = providers.Factory(
        EdgeLinkExecutionUpdateHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
        logger=infra.stdlib_logger,
    )

    create_user_handler_factory = providers.Factory(
        UserCreateHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
    )
    update_user_handler_factory = providers.Factory(
        UserUpdateHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
    )
    delete_user_handler_factory = providers.Factory(
        UserDeleteHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
    )
