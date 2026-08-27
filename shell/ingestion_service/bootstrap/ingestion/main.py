from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

import uvicorn

from shell.ingestion_service.bootstrap.ingestion.container.ingestion_core_container import (
    IngestionCoreContainer,
    configure_ingestion_container,
)
from shell.ingestion_service.framework.ingestion.api.app import create_ingestion_app
from shell.ingestion_service.infrastructure.ingestion.seed import seed_ingestion_dev_data
from shell.ingestion_service.migrations.baseline import run_ingestion_baseline
from shell.platform.infrastructure.configuration.shell_config import LoadedConfiguration
from shell.platform.infrastructure.messaging.event.event_worker import run_delivery_workers


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Ingestion BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8004)
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--worker", action="store_true")
    args = parser.parse_args()
    config = LoadedConfiguration.from_environment(
        Path(__file__).resolve().parent / "config", service_name="ingestion"
    )
    deployment = config.deployment
    runtime = config.platform_runtime
    service = config.service
    database_url = args.db_url or os.environ.get("INGESTION_SERVICE_DATABASE_URL") or deployment.database_url
    broker_url = os.environ.get("INGESTION_SERVICE_BROKER_URL") or runtime.events.broker_url
    api_key = os.environ.get("INGESTION_SERVICE_API_KEY") or config.auth.api_key
    if not api_key:
        raise ValueError("INGESTION_SERVICE_API_KEY is required")
    container = IngestionCoreContainer()
    container.config.db_url.from_value(database_url)
    container.config.broker_url.from_value(broker_url)
    container.config.worker_id.from_value("ingestion-event-processor")
    container.config.command_worker_id.from_value("ingestion-command-processor")
    container.config.worker_heartbeat_interval_seconds.from_value(
        runtime.events.worker_heartbeat_interval_seconds
    )
    container.config.worker_max_batch_time_seconds.from_value(
        runtime.events.worker_max_batch_time_seconds
    )
    configure_ingestion_container(container)
    app = create_ingestion_app(container, api_key=api_key)
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port))

    async def run() -> None:
        await run_ingestion_baseline(database_url)
        if service.seed_dev_data:
            await seed_ingestion_dev_data(database_url)
        if args.worker:
            await run_delivery_workers(
                workers=(
                    (
                        container.rabbit_inbox_consumer_factory(),
                        container.event_inbox_processor_factory(),
                        container.config.worker_id(),
                    ),
                    (
                        container.rabbit_command_inbox_consumer_factory(),
                        container.command_inbox_processor_factory(),
                        container.config.command_worker_id(),
                    ),
                ),
                session_factory=container.session_factory(),
                heartbeat_model=container.persistence_delivery_models().worker_heartbeat,
                poll_interval_seconds=runtime.events.worker_poll_interval,
                outbox_relay=container.outbox_to_transport_relay_factory(),
                outbox_worker_id="ingestion-outbox-relay",
            )
            return
        await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()
