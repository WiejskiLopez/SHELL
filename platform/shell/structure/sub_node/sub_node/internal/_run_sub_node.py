"""_run_sub_node.py
Responsible for one thing: invoking a runner on a single task node via subprocess
and updating the node status.
"""

import subprocess

from shell.utils.system.system import System
from shell.status.status import Status


def _run_sub_node(sub_node, task_dir, app, runner=None) -> Status:
    """Invoke the configured runner on this task node and update its status.

    Returns the resulting Status, or raises on fatal error.

    runner: optional callable (cmd, **kwargs) -> CompletedProcess for testability.
    """
    if runner is None:
        runner = subprocess.run

    command = sub_node.sub_node_command_.command_
    app.app_trace_.record_info('sub_node._run_sub_node._run_sub_node', f"running node {sub_node.node_name_} \u2192 {command}")

    try:
        proc = runner(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env={**System.env(), 'PYTHONUTF8': '1'},
            cwd=str(sub_node.entrypoint_path_.parent),
        )
        sub_node.node_status_.set_status(proc.returncode)
        app.app_trace_.record_info('sub_node._run_sub_node._run_sub_node', f"node {sub_node.node_name_} finished (rc={proc.returncode})", stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
        if proc.returncode != 0 and proc.stderr:
            app.app_trace_.record_info('sub_node._run_sub_node._run_sub_node', f"node {sub_node.node_name_} stderr: {proc.stderr.strip()}")
        if proc.returncode != 0 and proc.stdout:
            app.app_trace_.record_info('sub_node._run_sub_node._run_sub_node', f"node {sub_node.node_name_} stdout: {proc.stdout.strip()}")
        return sub_node.status_
    except Exception as exc:
        sub_node.node_status_.set_status(Status.ERROR)
        app.app_trace_.record_error_and_raise('sub_node._run_sub_node._run_sub_node', exc)
