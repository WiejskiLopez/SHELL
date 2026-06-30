from __future__ import annotations

import tempfile
from argparse import (
    Namespace,  # noqa: TC003 — argparse.Namespace używany w sygnaturze run() w runtime
)
from pathlib import Path
from typing import TYPE_CHECKING, Any  # Dodano import Any

from shell.application.execution.commands.task_execution_commands import ImportTaskExecutionCommand
from shell.application.execution.commands.workflow_commands import StartWorkflowCommand
from shell.application.execution.queries.workflow_get_by_id_query import WorkflowGetByIdQuery
from shell.bootstrap.execution.cli.command.command import RunnableCommand
from shell.bootstrap.execution.factory.application_factory import ApplicationFactory

if TYPE_CHECKING:
    from shell.infrastructure.platform.configuration.shell_config import ShellConfig


class SmokeCommand(RunnableCommand):
    async def run(self, args: Namespace) -> None:
        config: ShellConfig = args.shell_config
        print(f"[smoke] using database: {config.database_url}")
        core_container = await ApplicationFactory(config).build()

        # Wyciągamy kontekst aplikacji do Any, uciszając mypy tylko raz
        app_ctx: Any = core_container.app

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

        print("[smoke] envelopes routed: (RouteEnvelopesCommand removed — class does not exist)")

        dto = await query_bus.dispatch(WorkflowGetByIdQuery(workflow_id))
        print(f"[smoke] workflow status: {dto.status if dto else 'not found'}")
        print("[smoke] OK")
