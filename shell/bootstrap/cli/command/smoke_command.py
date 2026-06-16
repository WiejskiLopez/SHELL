# shell/bootstrap/cli/commands/smoke_command.py
import tempfile
from argparse import Namespace
from pathlib import Path

from shell.application.commands.commands import (
    ImportTaskCommand,
    RouteEnvelopesCommand,
    StartWorkflowCommand,
)
from shell.application.queries.queries import GetWorkflowQuery
from shell.bootstrap.cli.command.command import RunnableCommand
from shell.bootstrap.factory.application_factory import ApplicationFactory


class SmokeCommand(RunnableCommand):
    async def run(self, args: Namespace) -> None:
        print(f"[smoke] using database: {args.db_url}")
        core_container = await ApplicationFactory(database_url=args.db_url).build()
        command_bus = core_container.app.buses.command_bus()
        query_bus = core_container.app.buses.query_bus()

        with tempfile.TemporaryDirectory() as tmp:
            md = Path(tmp) / "smoke-task.md"
            md.write_text("# Smoke task\nThis is a smoke-test task.", encoding="utf-8")
            task_id = await command_bus.dispatch(
                ImportTaskCommand(md_path=str(md), task_name="smoke-task")
            )

        print(f"[smoke] task imported: {task_id}")
        workflow_id = await command_bus.dispatch(StartWorkflowCommand(task_id=task_id))
        print(f"[smoke] workflow started: {workflow_id}")

        routed = await command_bus.dispatch(RouteEnvelopesCommand(workflow_id=workflow_id))
        print(f"[smoke] envelopes routed: {routed}")

        dto = await query_bus.dispatch(GetWorkflowQuery(workflow_id))
        print(f"[smoke] workflow status: {dto.status if dto else 'not found'}")
        print("[smoke] OK")
