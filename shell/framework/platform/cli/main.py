"""Main CLI entrypoint for shell — dispatches to per-mode command handlers."""

from __future__ import annotations

import asyncio
import os
import sys
from typing import TYPE_CHECKING, Any  # Dodano import Any

from shell.bootstrap.execution.factory.application_factory import ApplicationFactory
from shell.bootstrap.platform.config_logging.setup_logging import setup_logging
from shell.framework.platform.cli.parser import build_parser
if TYPE_CHECKING:
    from shell.infrastructure.platform.configuration.shell_config import ShellConfig

if TYPE_CHECKING:
    from collections.abc import Sequence

# Map of mode-name → default runner root dir (relative to this file if available).
_MODE_RUNNER_ROOTS: dict[str, str] = {
    "agent": "agent",
    "planner": "planner",
    "router": "router",
    "tasker": "tasker",
    "tool": "tool",
    "worker": "worker",
}


def _get_config() -> ShellConfig:
    from shell.infrastructure.platform.configuration.shell_config import ShellConfig

    config = ShellConfig.from_environment()
    config.max_step = _get_max_step()
    return config


def _get_max_step() -> int:
    try:
        return int(os.environ.get("SHELL_MAX_STEP", "20"))
    except ValueError:
        return 20


async def _run_node(mode: str, argv: Sequence[str]) -> int:
    from shell.application.platform.commands.commands import RunGraphNodeExecutionCommand

    parser = build_parser(prog=f"shell {mode}")
    ns = parser.parse_args(list(argv))

    config = _get_config()
    max_step = ns.max_step if ns.max_step is not None else config.max_step
    config.max_step = max_step
    core_container = await ApplicationFactory(config).build()

    graph_node_execution_id = ns.node_dir or mode
    workflow_id = ns.workflow_id or "default"
    work_dir = ns.work_dir or os.getcwd()

    command = RunGraphNodeExecutionCommand(
        graph_node_execution_id=graph_node_execution_id,
        workflow_id=workflow_id,
        workspace_path=work_dir,
    )

    # Rzutowanie na Any wycisza błąd dynamicznego providera w jednym miejscu
    app_ctx: Any = core_container.app
    try:
        await app_ctx.buses.command_bus().dispatch(command)
        return 0
    except Exception as exception:  # noqa: BLE001 — celowe łapanie Exception w głównej pętli CLI dla _run_node
        print(f"ERROR: {exception}", file=sys.stderr)
        return 1


async def _import_task_execution(argv: Sequence[str]) -> int:
    from shell.application.platform.commands.commands import ImportTaskExecutionCommand

    parser = build_parser(prog="shell import-task")
    ns = parser.parse_args(list(argv))

    task_execution_name = ns.task_execution_name
    task_dir = ns.task_dir
    if not task_execution_name or not task_dir:
        print(
            "ERROR: --task-name and --task-dir are required for import-task_execution.",
            file=sys.stderr,
        )
        return 1

    import pathlib

    md_path = str(pathlib.Path(task_dir) / f"{task_execution_name}.md")

    config = _get_config()
    core_container = await ApplicationFactory(config).build()
    command = ImportTaskExecutionCommand(md_path=md_path, task_execution_name=task_execution_name)

    app_ctx: Any = core_container.app
    try:
        task_execution_id = await app_ctx.buses.command_bus().dispatch(command)
        print(f"Imported task '{task_execution_name}' with id={task_execution_id}")
        return 0
    except Exception as exception:  # noqa: BLE001 — celowe łapanie Exception w głównej pętli CLI dla _import_task_execution
        print(f"ERROR: {exception}", file=sys.stderr)
        return 1


async def _route(argv: Sequence[str]) -> int:
    from shell.application.platform.commands.commands import RouteEnvelopesCommand

    parser = build_parser(prog="shell route")
    ns = parser.parse_args(list(argv))

    config = _get_config()
    max_step = ns.max_step if ns.max_step is not None else config.max_step
    config.max_step = max_step
    core_container = await ApplicationFactory(config).build()

    workflow_id = ns.workflow_id or "default"
    command = RouteEnvelopesCommand(workflow_id=workflow_id)

    app_ctx: Any = core_container.app
    try:
        count = await app_ctx.buses.command_bus().dispatch(command)
        print(f"Routed {count} envelopes.")
        return 0
    except Exception as exception:  # noqa: BLE001 — celowe łapanie Exception w głównej pętli CLI dla _route
        print(f"ERROR: {exception}", file=sys.stderr)
        return 1


async def _run_tasker(argv: Sequence[str]) -> int:
    from shell.framework.execution.orchestration.sync_workflow_runner import SyncWorkflowRunner

    parser = build_parser(prog="shell run-tasker")
    ns = parser.parse_args(list(argv))

    task_execution_id = ns.task_execution_id
    if not task_execution_id:
        print("ERROR: --task-id is required for run-tasker.", file=sys.stderr)
        return 1

    work_dir = ns.work_dir or os.getcwd()

    config = _get_config()
    core_container = await ApplicationFactory(config).build()

    app_ctx: Any = core_container.app
    messaging_ctx: Any = core_container.messaging

    # Build the synchronous workflow runner
    runner = SyncWorkflowRunner(
        handler=app_ctx.commands.run_tasker_workflow_handler_factory(),
        relay=messaging_ctx.outbox_to_inbox_relay(),
        processor=messaging_ctx.inbox_processor(),
        unit_of_work=app_ctx.buses.unit_of_work_factory(),
    )

    try:
        result = await runner.run(
            task_execution_id=task_execution_id,
            work_dir=work_dir,
        )
        print(f"Workflow {result.workflow_id} [{result.status}]: {result.message}")
        return 0 if result.status == "done" else 1
    except Exception as exc:  # noqa: BLE001 — celowe łapanie Exception w głównej pętli CLI dla _run_tasker
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry-point — first positional arg is the mode/subcommand."""
    arguments = list(argv) if argv is not None else sys.argv[1:]
    setup_logging()
    if not arguments:
        print("Usage: shell <mode> [options]", file=sys.stderr)
        print(
            f"  modes: {', '.join(list(_MODE_RUNNER_ROOTS) + ['import-task', 'route'])}",
            file=sys.stderr,
        )
        return 1

    mode = arguments[0]
    rest = arguments[1:]

    if mode in _MODE_RUNNER_ROOTS:
        return asyncio.run(_run_node(mode, rest))
    elif mode == "import-task":
        return asyncio.run(_import_task_execution(rest))
    elif mode == "route":
        return asyncio.run(_route(rest))
    elif mode == "run-tasker":
        return asyncio.run(_run_tasker(rest))
    else:
        print(f"Unknown mode: {mode!r}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
