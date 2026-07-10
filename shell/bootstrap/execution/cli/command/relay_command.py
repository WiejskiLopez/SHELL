from __future__ import annotations

from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace używany w sygnaturze run() w runtime
)
from typing import TYPE_CHECKING

from shell.bootstrap.execution.cli.command.command import RunnableCommand
from shell.platform.bootstrap.database_config.database_bootstrap import bootstrap_database
from shell.platform.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
from shell.platform.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.platform.infrastructure.messaging.event.outbox_to_inbox_relay import OutboxToInboxRelay
from shell.platform.infrastructure.persistence.sql import build_session_factory

if TYPE_CHECKING:
    from shell.platform.infrastructure.configuration.shell_config import ShellConfig


class RelayCommand(RunnableCommand):
    async def run(self, args: Namespace) -> None:
        config: ShellConfig = args.shell_config
        await bootstrap_database(config)
        sf = build_session_factory(config.database_url)
        logger = StdlibLogger("shell.relay")
        downstream = CompositeEventPublisher([LoggingEventPublisher(logger)])

        relay = OutboxToInboxRelay(sf, downstream)
        count = await relay.run_once()
        print(f"[relay] processed {count} outbox event(s)")
