"""bootstrap/main.py — runnable module for smoke-testing and admin tasks.

Usage:
    python -m shell_ddd.bootstrap.main smoke [--db-url sqlite+aiosqlite:///smoke.db]
    python -m shell_ddd.bootstrap.main relay  [--db-url ...]  # process outbox once
"""
from __future__ import annotations

import asyncio
import sys
import tempfile
from pathlib import Path

from shell_ddd.bootstrap.database_bootstrap import bootstrap_database


async def _smoke(db_url: str) -> None:
    """End-to-end smoke test: import → start-workflow → route.

    Uses an in-memory task (no real filesystem reads) so it runs without
    any external files.
    """
    from shell_ddd.application.commands.commands import (
        ImportTaskCommand,
        RouteEnvelopesCommand,
        StartWorkflowCommand,
    )
    from shell_ddd.application.queries.queries import GetWorkflowQuery
    from shell_ddd.bootstrap.container import ApplicationFactory

    print(f"[smoke] using database: {db_url}")
    container = await ApplicationFactory(database_url=db_url).build()
    bus = container.command_bus
    qbus = container.query_bus

    # --- 1. Write a minimal .md / .yaml to a temp dir and import the task ---
    with tempfile.TemporaryDirectory() as tmp:
        md = Path(tmp) / "smoke-task.md"
        md.write_text("# Smoke task\nThis is a smoke-test task.", encoding="utf-8")
        yaml = Path(tmp) / "smoke-task.yaml"
        yaml.write_text("graph:\n  nodes: []\n", encoding="utf-8")

        task_id = await bus.dispatch(
            ImportTaskCommand(
                md_path=str(md),
                task_name="smoke-task",
            )
        )
    print(f"[smoke] task imported: {task_id}")

    # --- 2. Start a workflow ---
    workflow_id = await bus.dispatch(
        StartWorkflowCommand(task_name="smoke-task")
    )
    print(f"[smoke] workflow started: {workflow_id}")

    # --- 3. Route (0 envelopes expected for empty graph) ---
    routed = await bus.dispatch(
        RouteEnvelopesCommand(workflow_id=workflow_id)
    )
    print(f"[smoke] envelopes routed: {routed}")

    # --- 4. Query workflow status ---
    dto = await qbus.dispatch(GetWorkflowQuery(workflow_id))
    print(f"[smoke] workflow status: {dto.status if dto else 'not found'}")
    print("[smoke] OK")


async def _relay(db_url: str) -> None:
    """Process one batch of pending outbox events."""
    from shell_ddd.infrastructure.logging.composite_event_publisher import CompositeEventPublisher
    from shell_ddd.infrastructure.logging.logging_event_publisher import LoggingEventPublisher
    from shell_ddd.infrastructure.logging.stdlib_logger import StdlibLogger
    from shell_ddd.infrastructure.messaging.outbox_relay import OutboxRelay
    from shell_ddd.infrastructure.persistence.sql import build_session_factory, create_all_tables

    await bootstrap_database(db_url)
    sf = build_session_factory(db_url)
    logger = StdlibLogger("shell_ddd.relay")
    downstream = CompositeEventPublisher([LoggingEventPublisher(logger)])
    relay = OutboxRelay(sf, downstream)
    count = await relay.run_once()
    print(f"[relay] processed {count} outbox event(s)")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: python -m shell_ddd.bootstrap.main <command> [--db-url URL]")
        print("  smoke  — import→workflow→route end-to-end check")
        print("  relay  — process one batch of outbox events")
        return 0

    cmd = args[0]
    db_url = "sqlite+aiosqlite:///shell_ddd.db"
    for i, a in enumerate(args[1:], 1):
        if a == "--db-url" and i + 1 < len(args):
            db_url = args[i + 1]

    if cmd == "smoke":
        asyncio.run(_smoke(db_url))
        return 0
    elif cmd == "relay":
        asyncio.run(_relay(db_url))
        return 0
    else:
        print(f"Unknown command: {cmd!r}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
