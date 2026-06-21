from __future__ import annotations

import tempfile
from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace używany w sygnaturze run() w runtime
)
from pathlib import Path
from typing import Any  # Dodano import Any

from shell.application.platform.commands.commands import (
    ImportTaskExecutionCommand,
    RouteEnvelopesCommand,
    StartWorkflowCommand,
)
from shell.application.platform.queries.queries import GetWorkflowQuery
from shell.bootstrap.execution.cli.command.command import RunnableCommand
from shell.bootstrap.execution.factory.application_factory import ApplicationFactory


class SmokeCommand(RunnableCommand):
    async def run(self, args: Namespace) -> None:
        print(f"[smoke] using database: {args.db_url}")
        core_container = await ApplicationFactory(database_url=args.db_url).build()

        # Wyciągamy kontekst aplikacji do Any, uciszając mypy tylko raz
        app_ctx: Any = core_container.app  # type: ignore[attr-defined]

        command_bus = app_ctx.buses.command_bus()
        query_bus = app_ctx.buses.query_bus()

        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "smoke-task_execution.md"
            md.write_text("# Smoke task\nThis is a smoke-test task_execution.", encoding="utf-8")
            task_execution_id = await command_bus.dispatch(
                ImportTaskExecutionCommand(md_path=str(md), task_execution_name="smoke-task")
            )

        print(f"[smoke] task imported: {task_execution_id}")
        workflow_id = await command_bus.dispatch(
            StartWorkflowCommand(task_execution_id=task_execution_id)
        )
        print(f"[smoke] workflow started: {workflow_id}")

        routed = await command_bus.dispatch(RouteEnvelopesCommand(workflow_id=workflow_id))
        print(f"[smoke] envelopes routed: {routed}")

        dto = await query_bus.dispatch(GetWorkflowQuery(workflow_id))
        print(f"[smoke] workflow status: {dto.status if dto else 'not found'}")
        print("[smoke] OK")
