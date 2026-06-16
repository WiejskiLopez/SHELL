"""Shared argparse setup for all shell CLI entrypoints."""
from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def build_parser(prog: str = "shell") -> argparse.ArgumentParser:
    """Return a fully configured ArgumentParser with all shared flags."""
    parser = argparse.ArgumentParser(
        prog=prog,
        description="shell node runner.",
        add_help=True,
    )
    # ---- identity ----
    parser.add_argument("--node-dir", dest="node_dir", metavar="PATH", default=None)
    parser.add_argument("--mode", dest="mode", metavar="MODE", default=None)
    parser.add_argument("--role", dest="role", metavar="ROLE", default=None)
    parser.add_argument("--type", dest="type", metavar="TYPE", default=None)
    # ---- execution ----
    parser.add_argument("--model", dest="model", metavar="MODEL", default=None)
    parser.add_argument("--timeout", dest="timeout", type=int, metavar="SECONDS", default=None)
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=False)
    parser.add_argument("--log-level", dest="log_level", metavar="LEVEL", default="INFO")
    # ---- copilot/agent ----
    parser.add_argument("--no-ask-user", dest="no_ask_user", action="store_true", default=False)
    parser.add_argument("--autopilot", dest="autopilot", action="store_true", default=False)
    parser.add_argument("--add-dir", dest="add_dirs", metavar="PATH", action="append", default=[])
    parser.add_argument("--prompt", dest="prompt", metavar="PROMPT", default=None)
    parser.add_argument("--prompt-dir", dest="prompt_dir", metavar="PATH", default=None)
    # ---- task/source ----
    parser.add_argument("--source-dir", dest="source_dir", metavar="PATH", default=None)
    parser.add_argument("--task-name", dest="task_name", metavar="NAME", default=None)
    parser.add_argument("--task-id", dest="task_id", type=int, metavar="ID", default=None)
    parser.add_argument("--task-dir", dest="task_dir", metavar="PATH", default=None)
    parser.add_argument("--work-dir", dest="work_dir", metavar="PATH", default=None)
    # ---- routing ----
    parser.add_argument("--max-step", dest="max_step", type=int, metavar="N", default=None)
    parser.add_argument("--workflow-id", dest="workflow_id", metavar="ID", default=None)
    parser.add_argument("--envelope-id", dest="envelope_id", type=int, metavar="ID", default=None)
    parser.add_argument("--parent-thread-id", dest="parent_thread_id", metavar="ID", default=None)
    parser.add_argument("--parent-node-dir", dest="parent_node_dir", metavar="PATH", default=None)
    # ---- runner root (for entrypoint shims) ----
    parser.add_argument("--runner-root-dir", dest="runner_root_dir", metavar="PATH", default=None)
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    return build_parser().parse_args(argv)
