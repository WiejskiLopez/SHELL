"""_run_tool.py
Run the external tool defined in config.yaml.

Tools are lightweight executables that do NOT generate working logs.
Builds the subprocess command, runs it, captures output, and returns Status.
"""

from __future__ import annotations

import subprocess

from shell.status.status import Status


def _run_tool(tool, runner=None) -> Status:
    if runner is None:
        runner = subprocess.run

    app = tool._app
    app_properties = app.app_properties_
    node_dir = app.app_node_.node_.node_dir_

    cmd = _build_cmd(app_properties)

    env = None

    try:
        proc = runner(
            cmd,
            capture_output=True,
            text=True,
            timeout=app_properties.timeout_,
            encoding='utf-8',
            errors='replace',
            cwd=node_dir,
            env=env,
        )
        app.app_trace_.record_info(
            'tool._run_tool._run_tool',
            f'returncode={proc.returncode}',
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
        )
        if proc.stderr:
            app.app_trace_.record_warning(
                'tool._run_tool._run_tool',
                Exception(f"stderr (returncode={proc.returncode}): {proc.stderr.strip()}"),
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
            )
        return Status.from_returncode(proc.returncode)
    except subprocess.TimeoutExpired:
        return Status.from_returncode(2)
    except Exception as exc:
        app.app_trace_.record_error('tool._run_tool._run_tool', exc)
        return Status.from_returncode(1)


def _build_cmd(cfg) -> list[str]:
    return [cfg.command_]
