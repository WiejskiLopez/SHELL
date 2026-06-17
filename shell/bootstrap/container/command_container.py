"""Kontener obsługujący wyłącznie operacje zapisu (Command Handlers)."""

from __future__ import annotations

from dependency_injector import containers, providers

from shell.application.command_handlers.archive_envelope_handler import ArchiveEnvelopeHandler
from shell.application.command_handlers.bootstrap_runner_config_handler import (
    BootstrapRunnerConfigHandler,
)
from shell.application.command_handlers.import_task_execution_handler import (
    ImportTaskExecutionHandler,
)
from shell.application.command_handlers.route_envelopes_handler import RouteEnvelopesHandler
from shell.application.command_handlers.run_node_handler import RunNodeHandler
from shell.application.command_handlers.run_tasker_workflow_handler import (
    RunTaskerWorkflowHandler,
)
from shell.application.command_handlers.save_node_result_handler import SaveNodeResultHandler
from shell.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell.application.command_handlers.start_workflow_handler import StartWorkflowHandler


class CommandContainer(containers.DeclarativeContainer):
    """Kontener obsługujący wyłącznie operacje zapisu (Command Handlers)."""

    config = providers.Configuration()
    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

    import_task_execution_handler_factory = providers.Factory(
        ImportTaskExecutionHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        task_execution_loader=infra.task_execution_loader_factory,
        logger=infra.stdlib_logger,
    )
    start_workflow_handler_factory = providers.Factory(
        StartWorkflowHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        navigator=domain.node_navigator_factory,
    )
    route_envelopes_handler_factory = providers.Factory(
        RouteEnvelopesHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        max_step=config.max_step,
    )
    run_node_handler_factory = providers.Factory(
        RunNodeHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        workspace=infra.workspace_factory,
        runner=infra.runner_factory,
        strategy=domain.strategy,
    )
    archive_envelope_handler_factory = providers.Factory(
        ArchiveEnvelopeHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
    )
    save_node_result_handler_factory = providers.Factory(
        SaveNodeResultHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
    )
    save_prompt_handler_factory = providers.Factory(
        SavePromptHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
    )
    bootstrap_runner_config_handler_factory = providers.Factory(
        BootstrapRunnerConfigHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
    )
    run_tasker_workflow_handler_factory = providers.Factory(
        RunTaskerWorkflowHandler,
        uow=buses.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        navigator=domain.node_navigator_factory,
    )
