"""Kontener obsługujący wyłącznie operacje zapisu (Command Handlers)."""

from __future__ import annotations

from dependency_injector import containers, providers
from shell.application.definition.command_handlers.bootstrap_runner_config_handler import (
    BootstrapRunnerConfigHandler,
)
from shell.application.execution.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.execution.command_handlers.run_graph_node_execution_handler import (
    RunGraphNodeExecutionHandler,
)
from shell.application.execution.command_handlers.run_tasker_workflow_handler import (
    RunTaskerWorkflowHandler,
)
from shell.application.execution.command_handlers.save_graph_node_execution_result_handler import (
    SaveGraphNodeExecutionResultHandler,
)
from shell.application.execution.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell.application.execution.command_handlers.create_graph_node_execution_handler import (
    CreateGraphNodeExecutionCommandHandler,
)
from shell.application.execution.command_handlers.attach_graph_node_executions_handler import (
    AttachGraphNodeExecutionsCommandHandler,
)


class CommandContainer(containers.DeclarativeContainer):
    """Kontener obsługujący wyłącznie operacje zapisu (Command Handlers)."""

    config = providers.Configuration()
    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

    import_task_execution_handler_factory = providers.Factory(
        ImportTaskExecutionHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        task_execution_loader=infra.task_execution_loader_factory,
        logger=infra.stdlib_logger,
    )
    start_workflow_handler_factory = providers.Factory(
        StartWorkflowHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
    )
    run_graph_node_execution_handler_factory = providers.Factory(
        RunGraphNodeExecutionHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        workspace=infra.workspace_factory,
        runner=infra.runner_factory,
        strategy=domain.strategy,
    )
    save_graph_node_execution_result_handler_factory = providers.Factory(
        SaveGraphNodeExecutionResultHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
    )
    bootstrap_runner_config_handler_factory = providers.Factory(
        BootstrapRunnerConfigHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
    )
    run_tasker_workflow_handler_factory = providers.Factory(
        RunTaskerWorkflowHandler,
        unit_of_work=buses.unit_of_work_factory,
        clock=infra.clock_factory,
        id_generator=infra.id_generator_factory,
        navigator=domain.node_navigator_factory,
    )
    create_graph_node_execution_handler_factory = providers.Factory(
        CreateGraphNodeExecutionCommandHandler,
        unit_of_work=buses.unit_of_work_factory,
        identity=infra.id_generator_factory,
        time=infra.clock_factory,
    )
    attach_graph_node_executions_handler_factory = providers.Factory(
        AttachGraphNodeExecutionsCommandHandler,
        unit_of_work=buses.unit_of_work_factory,
        time=infra.clock_factory,
    )
