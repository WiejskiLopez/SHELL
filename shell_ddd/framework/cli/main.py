"""Main CLI entrypoint for shell_ddd — dispatches to per-mode command handlers."""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Sequence

from shell_ddd.framework.cli.parser import build_parser


# Map of mode-name → default runner root dir (relative to this file if available).
_MODE_RUNNER_ROOTS: dict[str, str] = {
    "agent": "agent",
    "router": "router",
    "tasker": "tasker",
    "tool": "tool",
    "worker": "worker",
}


def _get_database_url() -> str:
    return os.environ.get("SHELL_DDD_DATABASE_URL", "sqlite+aiosqlite:///shell_ddd.db")


def _get_max_step() -> int:
    try:
        return int(os.environ.get("SHELL_DDD_MAX_STEP", "20"))
    except ValueError:
        return 20


async def _run_node(mode: str, argv: Sequence[str]) -> int:
    from shell_ddd.bootstrap.container import ApplicationFactory
    from shell_ddd.application.commands.commands import RunNodeCommand

    parser = build_parser(prog=f"shell_ddd {mode}")
    ns = parser.parse_args(list(argv))

    database_url = _get_database_url()
    max_step = ns.max_step if ns.max_step is not None else _get_max_step()
    container = await ApplicationFactory(database_url=database_url, max_step=max_step).build()

    node_id = ns.node_dir or mode
    workflow_id = ns.workflow_id or "default"
    work_dir = ns.work_dir or os.getcwd()

    cmd = RunNodeCommand(
        node_id=node_id,
        workflow_id=workflow_id,
        workspace_path=work_dir,
    )
    try:
        await container.command_bus.dispatch(cmd)
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


async def _import_task(argv: Sequence[str]) -> int:
    from shell_ddd.bootstrap.container import ApplicationFactory
    from shell_ddd.application.commands.commands import ImportTaskCommand

    parser = build_parser(prog="shell_ddd import-task")
    ns = parser.parse_args(list(argv))

    task_name = ns.task_name
    task_dir = ns.task_dir
    if not task_name or not task_dir:
        print("ERROR: --task-name and --task-dir are required for import-task.", file=sys.stderr)
        return 1

    import pathlib
    md_path = str(pathlib.Path(task_dir) / f"{task_name}.md")
    yaml_path = str(pathlib.Path(task_dir) / f"{task_name}.yaml")

    database_url = _get_database_url()
    container = await ApplicationFactory(database_url=database_url).build()
    cmd = ImportTaskCommand(md_path=md_path, yaml_path=yaml_path, task_name=task_name)
    try:
        task_id = await container.command_bus.dispatch(cmd)
        print(f"Imported task '{task_name}' with id={task_id}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


async def _route(argv: Sequence[str]) -> int:
    from shell_ddd.bootstrap.container import ApplicationFactory
    from shell_ddd.application.commands.commands import RouteEnvelopesCommand

    parser = build_parser(prog="shell_ddd route")
    ns = parser.parse_args(list(argv))

    database_url = _get_database_url()
    max_step = ns.max_step if ns.max_step is not None else _get_max_step()
    container = await ApplicationFactory(database_url=database_url, max_step=max_step).build()

    workflow_id = ns.workflow_id or "default"
    cmd = RouteEnvelopesCommand(workflow_id=workflow_id)
    try:
        count = await container.command_bus.dispatch(cmd)
        print(f"Routed {count} envelopes.")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


async def _run_tasker(argv: Sequence[str]) -> int:
    from shell_ddd.bootstrap.container import ApplicationFactory
    from shell_ddd.application.commands.commands import RunTaskerWorkflowCommand

    parser = build_parser(prog="shell_ddd run-tasker")
    ns = parser.parse_args(list(argv))

    task_name = ns.task_name
    if not task_name:
        print("ERROR: --task-name is required for run-tasker.", file=sys.stderr)
        return 1

    work_dir = ns.work_dir or os.getcwd()
    try:
        max_parallel = int(os.environ.get("SHELL_DDD_MAX_PARALLEL", "4"))
    except ValueError:
        max_parallel = 4

    database_url = _get_database_url()
    container = await ApplicationFactory(database_url=database_url).build()
    cmd = RunTaskerWorkflowCommand(
        task_name=task_name,
        work_dir=work_dir,
        max_parallel=max_parallel,
    )
    try:
        workflow_id = await container.command_bus.dispatch(cmd)
        print(f"Tasker workflow completed: workflow_id={workflow_id}")
        return 0
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry-point — first positional arg is the mode/subcommand."""
    args = list(argv) if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: shell_ddd <mode> [options]", file=sys.stderr)
        print(f"  modes: {', '.join(list(_MODE_RUNNER_ROOTS) + ['import-task', 'route'])}", file=sys.stderr)
        return 1

    mode = args[0]
    rest = args[1:]

    if mode in _MODE_RUNNER_ROOTS:
        return asyncio.run(_run_node(mode, rest))
    elif mode == "import-task":
        return asyncio.run(_import_task(rest))
    elif mode == "route":
        return asyncio.run(_route(rest))
    elif mode == "run-tasker":
        return asyncio.run(_run_tasker(rest))
    else:
        print(f"Unknown mode: {mode!r}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
