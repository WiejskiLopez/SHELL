from __future__ import annotations

import logging
from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace used in run() signature at runtime
)
from typing import TYPE_CHECKING

from shell.execution_service.bootstrap.execution.cli.command.command import RunnableCommand

if TYPE_CHECKING:
    from shell.platform.infrastructure.configuration.config_slices import DeploymentConfig

logger = logging.getLogger(__name__)


class SmokeCommand(RunnableCommand):
    async def run(self, args: Namespace) -> None:
        deployment: DeploymentConfig = args.deployment_config
        logger.info("using database: %s", deployment.database_url)
        logger.info("smoke command runs in reduced mode (import/start commands removed)")
        logger.info("OK")
