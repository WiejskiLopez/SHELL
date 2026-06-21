from __future__ import annotations

from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace używany w sygnaturze run() w runtime
)
from typing import TYPE_CHECKING

from shell.bootstrap.execution.cli.command.command import RunnableCommand
from shell.bootstrap.platform.database_config.database_bootstrap import bootstrap_database
from shell.infrastructure.platform.logging.composite_event_publisher import CompositeEventPublisher
from shell.infrastructure.platform.logging.logging_event_publisher import LoggingEventPublisher
from shell.infrastructure.platform.logging.stdlib_logger import StdlibLogger
from shell.infrastructure.platform.messaging.outbox_to_inbox_relay import OutboxToInboxRelay
from shell.infrastructure.platform.persistence.sql import build_session_factory

if TYPE_CHECKING:
    from shell.infrastructure.platform.configuration.shell_config import ShellConfig


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
