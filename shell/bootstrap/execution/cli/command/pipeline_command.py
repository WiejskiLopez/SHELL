"""One-shot pipeline command: runs relay → processor once."""

from __future__ import annotations

import logging
from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace used in run() signature at runtime
)
from typing import TYPE_CHECKING

from shell.bootstrap.execution.cli.command.command import RunnableCommand
from shell.bootstrap.execution.factory.application_factory import ApplicationFactory

if TYPE_CHECKING:
    from shell.platform.infrastructure.configuration.shell_config import ShellConfig

logger = logging.getLogger(__name__)


class PipelineCommand(RunnableCommand):
    """Runs full outbox → inbox → eventbus pipeline once."""

    async def run(self, args: Namespace) -> None:
        config: ShellConfig = args.shell_config
        core_container = await ApplicationFactory(config).build()

        relay = core_container.events.outbox_to_inbox_relay()
        processor = core_container.events.inbox_processor()

        outbox_count = await relay.run_once()
        inbox_count = await processor.run_once()

        logger.info("outbox relay: %s events", outbox_count)
        logger.info("inbox processor: %s events", inbox_count)
