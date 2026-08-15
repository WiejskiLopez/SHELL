"""Entrypoint for the standalone User bounded context API."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING

import uvicorn

if TYPE_CHECKING:
    from shell.platform.infrastructure.messaging.transport.outbox_to_transport_relay import (
        OutboxToTransportRelay,
    )

from shell.platform.infrastructure.configuration.shell_config import ShellConfig
from shell.platform.infrastructure.messaging.event.event_worker import run_event_inbox_worker
from shell.platform.infrastructure.messaging.inbox.inbox_batch_result import (
    InboxBatchResult,
)
from shell.platform.infrastructure.messaging.inbox.inbox_legacy_migration import (
    InboxLegacyMigration,
    assert_inbox_ready,
)
from shell.platform.infrastructure.messaging.polling_worker import (
    PollingWorker,
    PollingWorkerConfig,
)
from shell.platform.infrastructure.messaging.worker_heartbeat import WorkerHeartbeatRecorder
from shell.user_service.bootstrap.user.container.user_core_container import (
    UserCoreContainer,
    configure_user_container,
)
from shell.user_service.framework.user.api.app import create_user_app
from shell.user_service.migrations.baseline import run_user_baseline


class _PollingOutboxRelay:
    """Adapt OutboxToTransportRelay to the PollingTask protocol."""

    def __init__(self, relay: OutboxToTransportRelay) -> None:
        self._relay = relay

    async def run_once(self) -> InboxBatchResult:
        count = await self._relay.run_once()
        return InboxBatchResult(
            claimed_count=count,
            processed_count=0,
            retried_count=0,
            dead_lettered_count=0,
            failed_count=0,
            duration_ms=0,
        )


async def _run_outbox_relay(container: UserCoreContainer) -> None:
    """Periodically deliver the User BC outbox to the broker (Faza 9)."""
    config = ShellConfig.from_environment(Path(__file__).resolve().parent / "config")
    worker_id = "user-outbox-relay"
    heartbeat = WorkerHeartbeatRecorder(
        container.session_factory(),
        container.persistence_delivery_models().worker_heartbeat,
        worker_id,
    )
    worker = PollingWorker(
        _PollingOutboxRelay(container.outbox_to_transport_relay_factory()),
        PollingWorkerConfig(
            worker_id=worker_id,
            poll_interval_seconds=config.events.worker_poll_interval,
        ),
        heartbeat=heartbeat.beat,
    )
    await worker.run()


async def _run_command_worker(container: UserCoreContainer) -> None:
    config = ShellConfig.from_environment(Path(__file__).resolve().parent / "config")
    await run_event_inbox_worker(
        consumer=container.rabbit_command_inbox_consumer_factory(),
        processor=container.command_inbox_processor_factory(),
        session_factory=container.session_factory(),
        heartbeat_model=container.persistence_delivery_models().worker_heartbeat,
        worker_id=container.config.command_worker_id(),
        poll_interval_seconds=config.events.worker_poll_interval,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell User BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--run-legacy-migration", action="store_true")
    args = parser.parse_args()

    config = ShellConfig.from_environment(Path(__file__).resolve().parent / "config")
    database_url = args.db_url or config.database_url

    container = UserCoreContainer()
    container.config.db_url.from_value(database_url)
    container.config.broker_url.from_value(config.events.broker_url)
    container.config.worker_id.from_value("user-outbox-relay")
    container.config.command_worker_id.from_value("user-command-processor")
    container.config.worker_heartbeat_interval_seconds.from_value(
        config.events.worker_heartbeat_interval_seconds
    )
    container.config.worker_max_batch_time_seconds.from_value(
        config.events.worker_max_batch_time_seconds
    )
    configure_user_container(container)
    app = create_user_app(
        container,
        api_key=config.api_key if args.api_key is None else args.api_key,
    )

    server = uvicorn.Server(
        uvicorn.Config(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
        )
    )

    async def run() -> None:
        await run_user_baseline(database_url)
        inbox_model = container.persistence_delivery_models().events.inbox
        if args.run_legacy_migration:
            counts = await InboxLegacyMigration(
                container.session_factory(), inbox_model
            ).classify_legacy_rows()
            print(f"inbox legacy migration counts: {counts}")
            await assert_inbox_ready(container.session_factory(), inbox_model)
            return
        if args.worker:
            await assert_inbox_ready(container.session_factory(), inbox_model)
            await asyncio.gather(_run_outbox_relay(container), _run_command_worker(container))
        else:
            await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()
