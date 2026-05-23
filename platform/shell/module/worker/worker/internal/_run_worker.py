"""_run_worker.py
Run the external script or process defined in worker.yaml.

Builds the subprocess command from WorkerConfig, runs it, captures output,
writes stdout to output/stdout.txt when capture includes stdout,
and returns Status based on returncode.
"""

from __future__ import annotations

import subprocess
import sys

from shell.status.status import Status


def _run_worker(worker, runner=None) -> Status:
    """Run the external process and return its Status.

    runner: optional callable with the same signature as subprocess.run (for testing).
    """
    if runner is None:
        runner = subprocess.run

    app = worker._app
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
            'worker._run_worker._run_worker',
            f'returncode={proc.returncode}',
            stdout=proc.stdout,
            stderr=proc.stderr,
            returncode=proc.returncode,
        )
        if proc.stderr:
            app.app_trace_.record_warning(
                'worker._run_worker._run_worker',
                Exception(f"stderr (returncode={proc.returncode}): {proc.stderr.strip()}"),
                stdout=proc.stdout,
                stderr=proc.stderr,
                returncode=proc.returncode,
            )
        return Status.from_returncode(proc.returncode)
    except subprocess.TimeoutExpired as exc:
        partial_out = exc.output or ''
        partial_err = exc.stderr or f'Timeout after {app_properties.timeout_}s'
        app.app_trace_.record_warning_and_raise('worker._run_worker._run_worker', exc, stdout=partial_out, stderr=partial_err)
    except OSError as exc:
        app.app_trace_.record_error_and_raise('worker._run_worker._run_worker', exc)
    except Exception as exc:  # noqa: BLE001
        app.app_trace_.record_error_and_raise('worker._run_worker._run_worker', exc)


def _build_cmd(cfg) -> list[str]:
    if cfg.type_ == 'python_module':
        return [sys.executable, '-m', cfg.command_]
    return [cfg.command_]
