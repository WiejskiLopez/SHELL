from shell_ddd.application.commands.commands import ImportTaskCommand, StartWorkflowCommand, RouteEnvelopesCommand, \
    RunNodeCommand, ArchiveEnvelopeCommand, SaveNodeResultCommand, SavePromptCommand, BootstrapRunnerConfigCommand, \
    RunTaskerWorkflowCommand
from shell_ddd.application.queries.queries import GetTaskByNameQuery, GetCurrentTaskQuery, GetWorkflowQuery, \
    GetEnvelopesByWorkflowQuery, GetNodeResultQuery, GetPromptQuery, GetRunnerConfigQuery, GetSessionHistoryQuery, \
    SearchSimilarQuery
from shell_ddd.bootstrap.core_container import CoreContainer
from shell_ddd.bootstrap.database_bootstrap import bootstrap_database


class ApplicationFactory:
    """Builds a CoreContainer for the given database URL."""

    def __init__(self, database_url: str, max_step: int = 0) -> None:
        self._database_url = database_url
        self._max_step = max_step

    async def build(self) -> CoreContainer:
        """Initialise the DB schema (if needed) and wire all components."""
        await bootstrap_database(self._database_url)

        core_container = CoreContainer()
        core_container.config.db_url.from_value(self._database_url)
        core_container.config.max_step.from_value(self._max_step)

        # REJESTRACJA KOMEND: Przekazujemy wskaźnik do fabryki (.provider)
        cmd_bus = core_container.command_bus()
        cmd_bus.register(ImportTaskCommand, core_container.import_task_handler_factory)
        cmd_bus.register(StartWorkflowCommand, core_container.start_workflow_handler_factory)
        cmd_bus.register(RouteEnvelopesCommand, core_container.route_envelopes_handler_factory)
        cmd_bus.register(RunNodeCommand, core_container.run_node_handler_factory)
        cmd_bus.register(ArchiveEnvelopeCommand, core_container.archive_envelope_handler_factory)
        cmd_bus.register(SaveNodeResultCommand, core_container.save_node_result_handler_factory)
        cmd_bus.register(SavePromptCommand, core_container.save_prompt_handler_factory)
        cmd_bus.register(BootstrapRunnerConfigCommand, core_container.bootstrap_runner_config_handler_factory)
        cmd_bus.register(RunTaskerWorkflowCommand, core_container.run_tasker_workflow_handler_factory)

        # REJESTRACJA ZAPYTAŃ: Przekazujemy wskaźnik do fabryki (.provider)
        q_bus = core_container.query_bus()
        q_bus.register(GetTaskByNameQuery, core_container.get_task_by_name_handler_factory)
        q_bus.register(GetCurrentTaskQuery, core_container.get_current_task_handler_factory)
        q_bus.register(GetWorkflowQuery, core_container.get_workflow_handler_factory)
        q_bus.register(GetEnvelopesByWorkflowQuery, core_container.get_envelopes_by_workflow_handler_factory)
        q_bus.register(GetNodeResultQuery, core_container.get_node_result_handler_factory)
        q_bus.register(GetPromptQuery, core_container.get_prompt_handler_factory)
        q_bus.register(GetRunnerConfigQuery, core_container.get_runner_config_handler_factory)
        q_bus.register(GetSessionHistoryQuery, core_container.get_session_history_handler_factory)
        q_bus.register(SearchSimilarQuery, core_container.search_similar_handler_factory)

        return core_container
