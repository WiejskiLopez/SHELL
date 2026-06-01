"""parse_args.py
Responsible for one thing: parsing CLI arguments for the agent node.
Returns a parsed ``argparse.Namespace`` object.
"""

import argparse
from typing import Sequence


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments and return a Namespace.

    Supported flags:
        --node-dir <PATH>  Path to the working node.
        --mode <MODE>      Runner mode (agent, tasker, router, worker).
        --role <ROLE>      Node role override.
        --type <TYPE>      Node type override.
        --version          Print the agent version and exit.
        --help             Print the agent help (manifest) and exit.
        --clean            Clean the node output/logs/tmp, then exit.
        --clean_out        Clean the node output/logs/tmp, then run normally.
        --dry-run          Simulate execution without writing output.
        --log-level <LVL>  Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        --no-ask-user      Do not generate questions; finish with SUCCESS or ERROR.
        --autopilot        Run in autonomous loop without user interaction.
        --add-dir <PATH>   Grant access to an additional directory (repeatable).
    """
    parser = argparse.ArgumentParser(
        prog="cli-agent",
        description="Stateless event-driven agent node (v2).",
        add_help=False,
    )
    
    parser.add_argument(
        "--node-dir",
        metavar="PATH",
        default=None,
        dest="node_dir",
        help="Path to the working node.",
    )

    parser.add_argument(
        "--mode",
        metavar="MODE",
        default=None,
        dest="mode",
        help="Runner mode: agent, tasker, router, or worker.",
    )

    parser.add_argument(
        "--role",
        metavar="ROLE",
        default=None,
        dest="role",
        help="Node role override.",
    )

    parser.add_argument(
        "--type",
        metavar="TYPE",
        default=None,
        dest="type",
        help="Node type override.",
    )
    
    parser.add_argument(
        "--version",
        action="store_true",
        help="Print the agent version and exit.",
    )

    parser.add_argument(
        "--help",
        action="store_true",
        dest="help",
        help="Print the agent help (manifest) and exit.",
    )

    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean output/, logs/ and tmp/, then exit.",
    )
    
    parser.add_argument(
        "--clean-out",
        action="store_true",
        dest="clean_out",
        help="Clean output/, logs/ and tmp/, then run normally.",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=False,
        dest="dry_run",
        help="Simulate execution without writing output files.",
    )
    
    parser.add_argument(
        "--log-level",
        metavar="LEVEL",
        default=None,
        dest="log_level",
        help="Log level: DEBUG, INFO, WARNING, ERROR, or CRITICAL.",
    )
    
    parser.add_argument(
        "--no-ask-user",
        action="store_true",
        default=False,
        dest="no_ask_user",
        help="Do not generate question files in output/0002_questions/.",
    )
    
    parser.add_argument(
        "--autopilot",
        action="store_true",
        default=True,
        help="Run Copilot in autonomous loop.",
    )

    parser.add_argument(
        "--add-dir",
        metavar="PATH",
        action="append",
        default=[],
        dest="add_dirs",
        help="Grant access to an additional directory (repeatable).",
    )

    parser.add_argument(
        "--prompt",
        metavar="PROMPT",
        default=None,
        dest="prompt",
        help="Prompt override: literal text, path to a file, or path to a directory.",
    )

    parser.add_argument(
        "--prompt-dir",
        metavar="PATH",
        default=None,
        dest="prompt_dir",
        help="Path to directory with *.prompt.md files; overrides default prompt folder.",
    )

    parser.add_argument(
        "--timeout",
        metavar="SECONDS",
        type=int,
        default=None,
        dest="timeout",
        help="Timeout for agent operations in seconds; default 120.",
    )

    # --- tasker-specific ---

    parser.add_argument(
        "--source-dir",
        metavar="PATH",
        default="c:/temp/source",
        dest="source_dir",
        help="Path to source directory containing task files.",
    )

    parser.add_argument(
        "--task-name",
        metavar="NAME",
        default=None,
        dest="task_name",
        help="Name of the task to execute (folder name in task repository).",
    )

    parser.add_argument(
        "--task-id",
        metavar="ID",
        type=int,
        default=None,
        dest="task_id",
        help="Task DB id; passed by parent tasker to subprocesses to load body from DB.",
    )

    # --- router-specific ---

    parser.add_argument(
        "--model",
        metavar="MODEL",
        default=None,
        dest="model",
        help="LLM model name; required in agent mode.",
    )

    # --- router-specific ---

    parser.add_argument(
        "--task-dir",
        metavar="PATH",
        default=None,
        dest="task_dir",
        help="Path to directory containing task files (.md and .yaml); required in router mode.",
    )

    parser.add_argument(
        "--work-dir",
        metavar="PATH",
        default=None,
        dest="work_dir",
        help="Working directory for agent operations.",
    )

    parser.add_argument(
        "--max-step",
        metavar="N",
        type=int,
        default=None,
        dest="max_step",
        help="Maximum TTL step for message routing; default 20.",
    )

    parser.add_argument(
        "--parent-thread-id",
        metavar="ID",
        default=None,
        dest="parent_thread_id",
        help="Timestamp-based thread id generated by tasker; propagated to all subprocesses.",
    )

    parser.add_argument(
        "--parent-node-dir",
        metavar="PATH",
        default=None,
        dest="parent_node_dir",
        help="Path to the parent tasker node directory; propagated to all subprocesses.",
    )

    return parser.parse_args(argv)
