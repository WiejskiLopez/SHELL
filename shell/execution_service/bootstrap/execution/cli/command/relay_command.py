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
from shell.platform.infrastructure.configuration.shell_config import LoadedConfiguration
from shell.platform.infrastructure.messaging.transport import OutboxToTransportRelay
from shell.platform.infrastructure.messaging.transport.rabbit import RabbitDeliveryTransport
from shell.platform.infrastructure.persistence.sql import build_session_factory

if TYPE_CHECKING:
    from shell.platform.infrastructure.configuration.config_slices import DeploymentConfig

logger = logging.getLogger(__name__)


class RelayCommand(RunnableCommand):
    async def run(self, args: Namespace) -> None:
        deployment: DeploymentConfig = args.deployment_config
        await run_execution_baseline(deployment.database_url)
        sf = build_session_factory(deployment.database_url)
        runtime = LoadedConfiguration.from_environment().platform_runtime
        transport = RabbitDeliveryTransport(runtime.events.broker_url)
        relay = OutboxToTransportRelay(
            sf,
            EVENT_DELIVERY_MODELS,
            transport,
            kind="event",
        )
        count = await relay.run_once()
        logger.info("processed %s outbox event(s)", count)
        await transport.close()
