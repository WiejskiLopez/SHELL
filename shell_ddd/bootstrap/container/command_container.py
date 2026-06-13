"""Kontener obsługujący wyłącznie operacje zapisu (Command Handlers)."""
from __future__ import annotations

from dependency_injector import containers, providers

from shell_ddd.application.command_handlers.archive_envelope_handler import ArchiveEnvelopeHandler
from shell_ddd.application.command_handlers.bootstrap_runner_config_handler import (
    BootstrapRunnerConfigHandler,
)
from shell_ddd.application.command_handlers.import_task_handler import ImportTaskHandler
from shell_ddd.application.command_handlers.route_envelopes_handler import RouteEnvelopesHandler
from shell_ddd.application.command_handlers.run_node_handler import RunNodeHandler
from shell_ddd.application.command_handlers.run_tasker_workflow_handler import (
    RunTaskerWorkflowHandler,
)
from shell_ddd.application.command_handlers.save_node_result_handler import SaveNodeResultHandler
from shell_ddd.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell_ddd.application.command_handlers.start_workflow_handler import StartWorkflowHandler


class CommandContainer(containers.DeclarativeContainer):
    """Kontener obsługujący wyłącznie operacje zapisu (Command Handlers)."""

    config = providers.Configuration()
    infra = providers.DependenciesContainer()
    domain = providers.DependenciesContainer()
    buses = providers.DependenciesContainer()

    import_task_handler_factory = providers.Factory(
        ImportTaskHandler,
        uow=infra.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        task_loader=infra.task_loader_factory,
        event_publisher=buses.event_publisher,
        logger=infra.stdlib_logger,
    )
    start_workflow_handler_factory = providers.Factory(
        StartWorkflowHandler,
        uow=infra.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        event_publisher=buses.event_publisher,
        navigator=domain.node_navigator_factory,
    )
    route_envelopes_handler_factory = providers.Factory(
        RouteEnvelopesHandler,
        uow=infra.uow_factory,
        clock=infra.clock_factory,
        event_publisher=buses.event_publisher,
        max_step=config.max_step,
    )
    run_node_handler_factory = providers.Factory(
        RunNodeHandler,
        uow=infra.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        workspace=infra.workspace_factory,
        runner=infra.runner_factory,
        strategy=domain.strategy,
        event_publisher=buses.event_publisher,
    )
    archive_envelope_handler_factory = providers.Factory(
        ArchiveEnvelopeHandler,
        uow=infra.uow_factory,
        clock=infra.clock_factory,
        event_publisher=buses.event_publisher,
    )
    save_node_result_handler_factory = providers.Factory(
        SaveNodeResultHandler,
        uow=infra.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        event_publisher=buses.event_publisher,
    )
    save_prompt_handler_factory = providers.Factory(
        SavePromptHandler,
        uow=infra.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
    )
    bootstrap_runner_config_handler_factory = providers.Factory(
        BootstrapRunnerConfigHandler,
        uow=infra.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
    )
    run_tasker_workflow_handler_factory = providers.Factory(
        RunTaskerWorkflowHandler,
        uow=infra.uow_factory,
        clock=infra.clock_factory,
        id_gen=infra.id_gen_factory,
        event_publisher=buses.event_publisher,
        navigator=domain.node_navigator_factory,
    )