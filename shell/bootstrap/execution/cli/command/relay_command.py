from __future__ import annotations

from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace używany w sygnaturze run() w runtime
)

from shell.bootstrap.execution.cli.command.command import RunnableCommand
from shell.bootstrap.platform.database_config.database_bootstrap import bootstrap_database
from shell.infrastructure.platform.logging.composite_event_publisher import CompositeEventPublisher
from shell.infrastructure.platform.logging.logging_event_publisher import LoggingEventPublisher
from shell.infrastructure.platform.logging.stdlib_logger import StdlibLogger
from shell.infrastructure.platform.messaging.outbox_to_inbox_relay import OutboxToInboxRelay
from shell.infrastructure.platform.persistence.sql import build_session_factory


class RelayCommand(RunnableCommand):
    async def run(self, args: Namespace) -> None:
        await bootstrap_database(args.db_url)
        sf = build_session_factory(args.db_url)
        logger = StdlibLogger("shell.relay")
        downstream = CompositeEventPublisher([LoggingEventPublisher(logger)])

        relay = OutboxToInboxRelay(sf, downstream)
        count = await relay.run_once()
        print(f"[relay] processed {count} outbox event(s)")
