from __future__ import annotations

from argparse import Namespace

from shell.bootstrap.cli.command.command import RunnableCommand
from shell.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
from shell.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
from shell.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.infrastructure.messaging.outbox_to_inbox_relay import OutboxToInboxRelay
from shell.infrastructure.persistence.sql import build_session_factory


class RelayCommand(RunnableCommand):
    async def run(self, args: Namespace) -> None:
        await bootstrap_database(args.db_url)
        sf = build_session_factory(args.db_url)
        logger = StdlibLogger("shell.relay")
        downstream = CompositeEventPublisher([LoggingEventPublisher(logger)])

        relay = OutboxToInboxRelay(sf, downstream)
        count = await relay.run_once()
        print(f"[relay] processed {count} outbox event(s)")
