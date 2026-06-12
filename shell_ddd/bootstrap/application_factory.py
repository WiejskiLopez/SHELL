# ==============================================================================
# ARCHIWUM — ten plik został zdekompozycjonowany do bootstrap/factory/.
# Wszystkie poniższe definicje są ZMIGROWANE i zakomentowane celowo.
# Aktywna implementacja: shell_ddd/bootstrap/factory/application_factory.py
# Szczegółowa rejestracja:
#   - komendy:  bootstrap/factory/command_factory.py
#   - zapytania: bootstrap/factory/query_factory.py
#   - eventy:   bootstrap/factory/event_factory.py
#   - orkiestrator szyn: bootstrap/factory/bus_factory.py
# ==============================================================================
from __future__ import annotations

# from shell_ddd.application.commands.commands import (
#     ArchiveEnvelopeCommand,
#     BootstrapRunnerConfigCommand,
#     ImportTaskCommand,
#     RouteEnvelopesCommand,
#     RunNodeCommand,
#     RunTaskerWorkflowCommand,
#     SaveNodeResultCommand,
#     SavePromptCommand,
#     StartWorkflowCommand,
# )
# from shell_ddd.application.queries.queries import (
#     GetCurrentTaskQuery,
#     GetEnvelopesByWorkflowQuery,
#     GetNodeResultQuery,
#     GetPromptQuery,
#     GetRunnerConfigQuery,
#     GetSessionHistoryQuery,
#     GetTaskByNameQuery,
#     GetWorkflowQuery,
#     SearchSimilarQuery,
# )
# from shell_ddd.bootstrap.container.core_container import CoreContainer
# from shell_ddd.bootstrap.database_bootstrap import bootstrap_database
# from shell_ddd.domain.events.events import (
#     EnvelopeExpired,
#     EnvelopeRouted,
#     NodeAdvanced,
#     NodeCompleted,
#     NodeExecutionRequested,
#     NodeFailed,
#     NodeStarted,
#     TaskCreated,
#     WorkflowCompleted,
#     WorkflowFailed,
#     WorkflowStarted,
# )
#
#
# class ApplicationFactory:
#     """Builds a CoreContainer for the given database URL."""
#
#     def __init__(self, database_url: str, max_step: int = 0) -> None:
#         self._database_url = database_url
#         self._max_step = max_step
#
#     async def build(self) -> CoreContainer:
#         """Initialise the DB schema (if needed) and wire all components."""
#         await bootstrap_database(self._database_url)
#
#         core_container = CoreContainer()
#         core_container.config.db_url.from_value(self._database_url)
#         core_container.config.max_step.from_value(self._max_step)
#
#         # REJESTRACJA KOMEND: Przekazujemy wskaźnik do fabryki (.provider)
#         cmd_bus = core_container.app.buses.command_bus()
#         cmd_bus.register(ImportTaskCommand, core_container.app.commands.import_task_handler_factory)
#         cmd_bus.register(StartWorkflowCommand, core_container.app.commands.start_workflow_handler_factory)
#         cmd_bus.register(RouteEnvelopesCommand, core_container.app.commands.route_envelopes_handler_factory)
#         cmd_bus.register(RunNodeCommand, core_container.app.commands.run_node_handler_factory)
#         cmd_bus.register(ArchiveEnvelopeCommand, core_container.app.commands.archive_envelope_handler_factory)
#         cmd_bus.register(SaveNodeResultCommand, core_container.app.commands.save_node_result_handler_factory)
#         cmd_bus.register(SavePromptCommand, core_container.app.commands.save_prompt_handler_factory)
#         cmd_bus.register(BootstrapRunnerConfigCommand, core_container.app.commands.bootstrap_runner_config_handler_factory)
#         cmd_bus.register(RunTaskerWorkflowCommand, core_container.app.commands.run_tasker_workflow_handler_factory)
#
#         # REJESTRACJA ZAPYTAŃ: Przekazujemy wskaźnik do fabryki (.provider)
#         q_bus = core_container.app.buses.query_bus()
#         q_bus.register(GetTaskByNameQuery, core_container.app.queries.get_task_by_name_handler_factory)
#         q_bus.register(GetCurrentTaskQuery, core_container.app.queries.get_current_task_handler_factory)
#         q_bus.register(GetWorkflowQuery, core_container.app.queries.get_workflow_handler_factory)
#         q_bus.register(GetEnvelopesByWorkflowQuery, core_container.app.queries.get_envelopes_by_workflow_handler_factory)
#         q_bus.register(GetNodeResultQuery, core_container.app.queries.get_node_result_handler_factory)
#         q_bus.register(GetPromptQuery, core_container.app.queries.get_prompt_handler_factory)
#         q_bus.register(GetRunnerConfigQuery, core_container.app.queries.get_runner_config_handler_factory)
#         q_bus.register(GetSessionHistoryQuery, core_container.app.queries.get_session_history_handler_factory)
#         q_bus.register(SearchSimilarQuery, core_container.app.queries.search_similar_handler_factory)
#
#         # REJESTRACJA EVENTÓW: subskrybenci EventBus
#         e_bus = core_container.app.buses.event_bus()
#         e_bus.subscribe(EnvelopeRouted, core_container.app.events.archive_on_delivered_handler_factory)
#         e_bus.subscribe(EnvelopeRouted, core_container.app.events.log_audit_handler_factory)
#         e_bus.subscribe(EnvelopeExpired, core_container.app.events.log_audit_handler_factory)
#         e_bus.subscribe(NodeCompleted, core_container.app.events.log_audit_handler_factory)
#         e_bus.subscribe(NodeFailed, core_container.app.events.log_audit_handler_factory)
#         e_bus.subscribe(TaskCreated, core_container.app.events.log_audit_handler_factory)
#         e_bus.subscribe(TaskCreated, core_container.app.events.build_graph_on_task_created_factory)
#         e_bus.subscribe(WorkflowStarted, core_container.app.events.log_audit_handler_factory)
#         e_bus.subscribe(WorkflowCompleted, core_container.app.events.log_audit_handler_factory)
#         e_bus.subscribe(WorkflowFailed, core_container.app.events.log_audit_handler_factory)
#         e_bus.subscribe(NodeStarted, core_container.app.events.log_audit_handler_factory)
#         e_bus.subscribe(NodeAdvanced, core_container.app.events.log_audit_handler_factory)
#         e_bus.subscribe(NodeExecutionRequested, core_container.app.events.node_execution_worker_factory)
#
#         return core_container
