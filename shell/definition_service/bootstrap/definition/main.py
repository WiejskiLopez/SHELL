"""Entrypoint for the standalone Definition bounded context API."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

import uvicorn

from shell.definition_service.bootstrap.definition.container.definition_core_container import (
    DefinitionCoreContainer,
    configure_definition_container,
)
from shell.definition_service.framework.definition.api.app import create_definition_app
from shell.definition_service.infrastructure.definition.seed import seed_definition_dev_data
from shell.definition_service.migrations.baseline import run_definition_baseline
from shell.platform.framework.bootstrap.server import build_service_uvicorn_config
from shell.platform.infrastructure.configuration.shell_config import LoadedConfiguration
from shell.platform.infrastructure.messaging.polling_worker import (
    PollingWorker,
    PollingWorkerConfig,
)
from shell.platform.infrastructure.messaging.worker_heartbeat import WorkerHeartbeatRecorder


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Definition BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8002)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()

    config = LoadedConfiguration.from_environment(
        Path(__file__).resolve().parent / "config", service_name="definition"
    )
    deployment = config.deployment
    runtime = config.platform_runtime
    service = config.service
    database_url = (
        args.db_url or os.environ.get("DEFINITION_SERVICE_DATABASE_URL") or deployment.database_url
    )
    broker_url = os.environ.get("DEFINITION_SERVICE_BROKER_URL") or runtime.events.broker_url
    api_key = os.environ.get("DEFINITION_SERVICE_API_KEY") or config.auth.api_key
    if not api_key:
        raise ValueError("DEFINITION_SERVICE_API_KEY is required")
    container = DefinitionCoreContainer()
    container.config.db_url.from_value(database_url)
    container.config.broker_url.from_value(broker_url)
    container.config.worker_id.from_value("definition-event-processor")
    container.config.worker_heartbeat_interval_seconds.from_value(
        runtime.events.worker_heartbeat_interval_seconds
    )
    container.config.worker_max_batch_time_seconds.from_value(
        runtime.events.worker_max_batch_time_seconds
    )
    configure_definition_container(container)
    app = create_definition_app(container, api_key=api_key)
    server = uvicorn.Server(
        build_service_uvicorn_config(
            app,
            service="definition",
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
    )

    async def run() -> None:
        await run_definition_baseline(database_url)
        if service.seed_dev_data:
            await seed_definition_dev_data(database_url)
        if args.worker:
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
                        poll_interval_seconds=runtime.events.worker_poll_interval,
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
