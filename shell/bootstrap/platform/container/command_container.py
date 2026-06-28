"""Kontener obsługujący wyłącznie operacje zapisu (Command Handlers)."""

from __future__ import annotations

from dependency_injector import containers, providers
from shell.application.definition.command_handlers.create_graph_definition_handler import (
    CreateGraphDefinitionHandler,
)
from shell.application.definition.command_handlers.runner_config_bootstrap_handler import (
    RunnerConfigBootstrapHandler,
)
from shell.application.execution.command_handlers.graph_node_execution_attach_handler import (
    GraphNodeExecutionAttachHandler,
)
from shell.application.execution.command_handlers.graph_node_execution_create_handler import (
    GraphNodeExecutionCreateHandler,
)
from shell.application.execution.command_handlers.graph_node_execution_run_handler import (
    GraphNodeExecutionRunHandler,
)
from shell.application.execution.command_handlers.graph_node_execution_save_result_handler import (
    GraphNodeExecutionSaveResultHandler,
)
from shell.application.execution.command_handlers.task_execution_import_handler import (
    TaskExecutionImportHandler,
)
from shell.application.execution.command_handlers.workflow_run_tasker_handler import (
    WorkflowRunTaskerHandler,
)
from shell.application.execution.command_handlers.workflow_start_handler import WorkflowStartHandler


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
    run_graph_node_execution_handler_factory = providers.Factory(
        GraphNodeExecutionRunHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        workspace=infra.workspace_factory,
        runner=infra.runner_factory,
        strategy=domain.strategy,
    )
    save_graph_node_execution_result_handler_factory = providers.Factory(
        GraphNodeExecutionSaveResultHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
    )
    create_graph_definition_handler_factory = providers.Factory(
        CreateGraphDefinitionHandler,
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
    create_graph_node_execution_handler_factory = providers.Factory(
        GraphNodeExecutionCreateHandler,
        unit_of_work=buses.unit_of_work_factory,
        identity=infra.id_generator_factory,
        time=infra.clock_factory,
    )
    attach_graph_node_executions_handler_factory = providers.Factory(
        GraphNodeExecutionAttachHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
    )
