"""Entrypoint for the standalone Session bounded context API."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, cast

import uvicorn

from shell.platform.infrastructure.configuration.shell_config import ShellConfig
from shell.platform.infrastructure.messaging.event.event_worker import run_delivery_workers
from shell.platform.infrastructure.messaging.inbox.inbox_legacy_migration import (
    InboxLegacyMigration,
    assert_inbox_ready,
)
from shell.session.bootstrap.session.container.session_core_container import (
    SessionCoreContainer,
    configure_session_container,
)
from shell.session.framework.session.api.app import create_session_app
from shell.session.migrations.baseline import run_session_baseline

if TYPE_CHECKING:
    from shell.platform.infrastructure.messaging.inbox.inbox_claim_service import (
        InboxStateModel,
    )


async def _run_event_worker(container: SessionCoreContainer) -> None:
    """Consume cross-BC events from the broker and process the local inbox."""
    config = ShellConfig.from_environment(Path(__file__).resolve().parent / "config")

    await run_delivery_workers(
        workers=(
            (
                container.rabbit_inbox_consumer_factory(),
                container.event_inbox_processor_factory(),
                "session-event-processor",
            ),
            (
                container.rabbit_command_inbox_consumer_factory(),
                container.command_inbox_processor_factory(),
                "session-command-processor",
            ),
        ),
        session_factory=container.session_factory(),
        heartbeat_model=container.persistence_delivery_models().worker_heartbeat,
        poll_interval_seconds=config.events.worker_poll_interval,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Shell Session BC API server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8003)
    parser.add_argument("--reload", action="store_true")
    parser.add_argument("--db-url", default=None)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--run-legacy-migration", action="store_true")
    args = parser.parse_args()
    config = ShellConfig.from_environment(Path(__file__).resolve().parent / "config")
    database_url = args.db_url or config.database_url
    container = SessionCoreContainer()
    container.config.db_url.from_value(database_url)
    container.config.broker_url.from_value(config.events.broker_url)
    container.config.worker_heartbeat_interval_seconds.from_value(
        config.events.worker_heartbeat_interval_seconds
    )
    container.config.worker_max_batch_time_seconds.from_value(
        config.events.worker_max_batch_time_seconds
    )
    container.config.worker_id.from_value("session-event-processor")
    container.config.command_worker_id.from_value("session-command-processor")
    configure_session_container(container)
    app = create_session_app(container)
    server = uvicorn.Server(uvicorn.Config(app, host=args.host, port=args.port, reload=args.reload))

    async def run() -> None:
        await run_session_baseline(database_url)
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
            print("inbox legacy migration complete — LEGACY_REVIEW == 0")
            return
        if args.worker:
            await assert_inbox_ready(container.session_factory(), inbox_model)
            await _run_event_worker(container)
        else:
            await server.serve()

    asyncio.run(run())


if __name__ == "__main__":
    main()
