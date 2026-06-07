"""ApplicationFactory — wires all handlers, ports, and adapters together."""
from __future__ import annotations

from dataclasses import dataclass

from shell_ddd.infrastructure.persistence.sql.query_services import SqlQueryServices

from shell_ddd.infrastructure.external.hash_embedder import HashEmbedder

from shell_ddd.application.bus import CommandBus, EventBus, QueryBus
from shell_ddd.application.command_handlers.archive_envelope_handler import ArchiveEnvelopeHandler
from shell_ddd.application.command_handlers.bootstrap_runner_config_handler import (
    BootstrapRunnerConfigHandler,
)
from shell_ddd.application.command_handlers.import_task_handler import ImportTaskHandler
from shell_ddd.application.command_handlers.route_envelopes_handler import RouteEnvelopesHandler
from shell_ddd.application.command_handlers.run_node_handler import RunNodeHandler
from shell_ddd.application.command_handlers.run_tasker_workflow_handler import RunTaskerWorkflowHandler
from shell_ddd.application.command_handlers.save_node_result_handler import SaveNodeResultHandler
from shell_ddd.application.command_handlers.save_prompt_handler import SavePromptHandler
from shell_ddd.application.command_handlers.start_workflow_handler import StartWorkflowHandler
from shell_ddd.application.commands.commands import (
    ArchiveEnvelopeCommand,
    BootstrapRunnerConfigCommand,
    ImportTaskCommand,
    RouteEnvelopesCommand,
    RunNodeCommand,
    RunTaskerWorkflowCommand,
    SaveNodeResultCommand,
    SavePromptCommand,
    StartWorkflowCommand,
)
from shell_ddd.application.queries.queries import (
    GetCurrentTaskQuery,
    GetEnvelopesByWorkflowQuery,
    GetNodeResultQuery,
    GetPromptQuery,
    GetRunnerConfigQuery,
    GetTaskByNameQuery,
    GetWorkflowQuery,
    GetSessionHistoryQuery,
    SearchSimilarQuery,

)
from shell_ddd.application.query_handlers.query_handlers import (
    GetCurrentTaskHandler,
    GetEnvelopesByWorkflowHandler,
    GetNodeResultHandler,
    GetPromptHandler,
    GetRunnerConfigHandler,
    GetTaskByNameHandler,
    GetWorkflowHandler,
    GetSessionHistoryHandler,
    SearchSimilarHandler,
)
from shell_ddd.application.strategies.node_execution_strategy import get_strategy
from shell_ddd.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
from shell_ddd.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
from shell_ddd.infrastructure.logging.sql_audit_publisher import SqlAuditPublisher
from shell_ddd.infrastructure.logging.stdlib_logger import StdlibLogger
from shell_ddd.infrastructure.persistence import SqlAlchemyUnitOfWork
from shell_ddd.infrastructure.persistence.sql import build_session_factory, create_all_tables


@dataclass
class Container:
    """Assembled application container."""

    command_bus: CommandBus
    query_bus: QueryBus
    event_bus: EventBus


class ApplicationFactory:
    """Builds a Container for the given database URL.

    Supports:
    - ``sqlite+aiosqlite:///path/to/db``
    - ``postgresql+asyncpg://user:pass@host/db``
    """

    def __init__(self, database_url: str, max_step: int = 0) -> None:
        self._database_url = database_url
        self._max_step = max_step
        self._embedder = HashEmbedder()

    async def build(self) -> Container:
        """Initialise the DB schema (if needed) and wire all components."""
        await create_all_tables(self._database_url)
        session_factory = build_session_factory(self._database_url)

        query_services = SqlQueryServices(session_factory)

        from shell_ddd.infrastructure.persistence.memory.memory import (
            FakeClock,
            FakeIdGenerator,
            FakeTaskLoader,
        )

        # Concrete adapters
        uow = SqlAlchemyUnitOfWork(session_factory)
        clock = FakeClock.__new__(FakeClock)  # placeholder; replace with SystemClock below

        from shell_ddd.infrastructure.time.system_clock import SystemClock

        clock = SystemClock()
        id_gen = FakeIdGenerator()  # placeholder; real UUID generator below

        from shell_ddd.shared.ids import UuidIdGenerator

        id_gen = UuidIdGenerator()

        event_bus = EventBus()
        stdlib_logger = StdlibLogger("shell_ddd")
        event_publisher: CompositeEventPublisher = CompositeEventPublisher(
            [
                LoggingEventPublisher(stdlib_logger),
                SqlAuditPublisher(session_factory),
                _EventBusPublisher(event_bus),
            ]
        )

        task_loader = FakeTaskLoader()  # replaced by real FS loader when available

        # Build default node execution strategy (agent by default — CLI sets per node)
        strategy = get_strategy("agent")

        # Fake workspace / runner — replaced by real adapters in Faza 4
        from shell_ddd.infrastructure.persistence.memory.memory import FakeNodeProcessRunner, FakeNodeWorkspace  # noqa: F401

        workspace = FakeNodeWorkspace()
        runner = FakeNodeProcessRunner()

        # Command bus
        command_bus = CommandBus()
        command_bus.register(
            ImportTaskCommand,
            ImportTaskHandler(uow, clock, id_gen, task_loader, event_publisher),
        )
        command_bus.register(
            StartWorkflowCommand,
            StartWorkflowHandler(uow, clock, id_gen, event_publisher),
        )
        command_bus.register(
            RouteEnvelopesCommand,
            RouteEnvelopesHandler(uow, clock, event_publisher, self._max_step),
        )
        command_bus.register(
            RunNodeCommand,
            RunNodeHandler(uow, clock, id_gen, workspace, runner, strategy, event_publisher),
        )
        command_bus.register(
            ArchiveEnvelopeCommand,
            ArchiveEnvelopeHandler(uow, clock, event_publisher),
        )
        command_bus.register(
            SaveNodeResultCommand,
            SaveNodeResultHandler(uow, clock, id_gen, event_publisher),
        )
        command_bus.register(
            SavePromptCommand,
            SavePromptHandler(uow, clock, id_gen),
        )
        command_bus.register(
            BootstrapRunnerConfigCommand,
            BootstrapRunnerConfigHandler(uow, clock, id_gen),
        )
        command_bus.register(
            RunTaskerWorkflowCommand,
            RunTaskerWorkflowHandler(uow, clock, id_gen, runner, event_publisher),
        )

        # Query bus
        query_bus = QueryBus()
        query_bus.register(
            GetTaskByNameQuery,
            GetTaskByNameHandler(queries=query_services)
        )
        query_bus.register(
            GetCurrentTaskQuery,
            GetCurrentTaskHandler(queries=query_services)
        )
        query_bus.register(
            GetWorkflowQuery,
            GetWorkflowHandler(queries=query_services)
        )
        query_bus.register(
            GetEnvelopesByWorkflowQuery,
            GetEnvelopesByWorkflowHandler(queries=query_services)
        )
        query_bus.register(
            GetNodeResultQuery,
            GetNodeResultHandler(queries=query_services)
        )
        query_bus.register(
            GetPromptQuery,
            GetPromptHandler(queries=query_services)
        )
        query_bus.register(
            GetRunnerConfigQuery,
            GetRunnerConfigHandler(queries=query_services)
        )
        query_bus.register(
           GetSessionHistoryQuery,
           GetSessionHistoryHandler(queries=query_services)
        )
        query_bus.register(
           SearchSimilarQuery,
           SearchSimilarHandler(queries=query_services, embedder=self._embedder)
        )

        return Container(
            command_bus=command_bus,
            query_bus=query_bus,
            event_bus=event_bus,
        )


class _EventBusPublisher:
    """Adapts EventBus to the EventPublisher port."""

    def __init__(self, bus: EventBus) -> None:
        self._bus = bus

    async def publish(self, events: list) -> None:
        await self._bus.publish(events)
