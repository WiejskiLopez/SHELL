"""Entrypoint for the standalone Definition bounded context API."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, cast

import uvicorn

from shell.definition_service.bootstrap.definition.container.definition_core_container import (
    DefinitionCoreContainer,
    configure_definition_container,
)
from shell.definition_service.framework.definition.api.app import create_definition_app
from shell.definition_service.migrations.baseline import run_definition_baseline
from shell.platform.infrastructure.configuration.shell_config import ShellConfig
from shell.platform.infrastructure.messaging.inbox.inbox_legacy_migration import (
    InboxLegacyMigration,
    assert_inbox_ready,
)
from shell.platform.infrastructure.messaging.polling_worker import (
    PollingWorker,
    PollingWorkerConfig,
)
from shell.platform.infrastructure.messaging.worker_heartbeat import WorkerHeartbeatRecorder

if TYPE_CHECKING:
    from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import (
        InboxStateModel,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Definition BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--run-legacy-migration", action="store_true")
    args = parser.parse_args()

    config = ShellConfig.from_environment(Path(__file__).resolve().parent / "config")
    database_url = args.db_url or config.database_url
    container = DefinitionCoreContainer()
    container.config.db_url.from_value(database_url)
    container.config.broker_url.from_value(config.events.broker_url)
    container.config.worker_id.from_value("definition-event-processor")
    container.config.worker_heartbeat_interval_seconds.from_value(
        config.events.worker_heartbeat_interval_seconds
    )
    container.config.worker_max_batch_time_seconds.from_value(
        config.events.worker_max_batch_time_seconds
    )
    configure_definition_container(container)
    app = create_definition_app(container)
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port, reload=args.reload))

    async def run() -> None:
        await run_definition_baseline(database_url)
        inbox_model = cast(
            "type[InboxStateModel]",
            container.persistence_delivery_models().events.inbox,
        )
        if args.run_legacy_migration:
            counts = await InboxLegacyMigration(
                container.session_factory(), inbox_model
            ).classify_legacy_rows()
            print(f"inbox legacy migration counts: {counts}")
            await assert_inbox_ready(container.session_factory(), inbox_model)
            return
        if args.worker:
            await assert_inbox_ready(container.session_factory(), inbox_model)
            consumer = container.rabbit_inbox_consumer_factory()
            await consumer.start()
            try:
                heartbeat = WorkerHeartbeatRecorder(
                    container.session_factory(),
                    container.persistence_delivery_models().worker_heartbeat,
                    container.config.worker_id(),
                )
                await PollingWorker(
                    container.event_inbox_processor_factory(),
                    PollingWorkerConfig(
                        worker_id=container.config.worker_id(),
                        poll_interval_seconds=config.events.worker_poll_interval,
                    ),
                    heartbeat=heartbeat.beat,
                ).run()
            finally:
                await consumer.close()
            return
        await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()
