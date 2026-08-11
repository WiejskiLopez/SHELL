from __future__ import annotations

import logging
from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace used in run() signature at runtime
)
from typing import TYPE_CHECKING

from shell.execution.bootstrap.execution.cli.command.command import RunnableCommand

if TYPE_CHECKING:
    from shell.platform.infrastructure.configuration.shell_config import ShellConfig

logger = logging.getLogger(__name__)


class SmokeCommand(RunnableCommand):
    async def run(self, args: Namespace) -> None:
        config: ShellConfig = args.shell_config
        logger.info("using database: %s", config.database_url)
        logger.info("smoke command runs in reduced mode (import/start commands removed)")
        logger.info("OK")
