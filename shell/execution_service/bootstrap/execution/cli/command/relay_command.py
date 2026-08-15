from __future__ import annotations

import logging
from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace used in run() signature at runtime
)
from typing import TYPE_CHECKING

from shell.execution_service.bootstrap.execution.cli.command.command import RunnableCommand
from shell.execution_service.infrastructure.execution.persistence.sql.models.base import (
    EVENT_DELIVERY_MODELS,
)
from shell.execution_service.migrations.baseline import run_execution_baseline
from shell.platform.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
from shell.platform.infrastructure.logging.stdlib_logger import StdlibLogger
from shell.platform.infrastructure.messaging.event.event_outbox_to_inbox_relay import (
    EventOutboxToInboxRelay,
)
from shell.platform.infrastructure.persistence.sql import build_session_factory

if TYPE_CHECKING:
    from shell.platform.infrastructure.configuration.shell_config import ShellConfig

logger = logging.getLogger(__name__)


class RelayCommand(RunnableCommand):
    async def run(self, args: Namespace) -> None:
        config: ShellConfig = args.shell_config
        await run_execution_baseline(config.database_url)
        sf = build_session_factory(config.database_url)
        relay_logger = StdlibLogger("shell.relay")
        downstream = LoggingEventPublisher(relay_logger)

        relay = EventOutboxToInboxRelay(sf, EVENT_DELIVERY_MODELS, downstream)
        count = await relay.run_once()
        logger.info("processed %s outbox event(s)", count)
