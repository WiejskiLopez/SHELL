"""_run_once.py
Responsible for one thing: running a CLI command once via subprocess.
Writes stdout, stderr, returncode to app.
On any error sets warning status.
"""

import subprocess

from shell.status.status import Status


def _run_once(
    cmd: list[str],
    prompt: str,
    timeout: int,
    app,
    runner=None,
) -> Status:
    if runner is None:
        runner = subprocess.run
    node_dir = app.app_node_.node_.node_dir_
    try:
        proc = runner(
            cmd,
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding="utf-8",
            errors="replace",
            cwd=node_dir,
        )
        app.app_trace_.record_info('agent._run_once._run_once', f'returncode={proc.returncode}', stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
        if proc.stdout and proc.stdout.strip():
            app.app_trace_.record_info('agent._run_once._run_once', f'stdout:\n{proc.stdout.strip()}', stdout=proc.stdout, returncode=proc.returncode)
        if proc.stderr:
            if proc.returncode == 0:
                app.app_trace_.record_info('agent._run_once._run_once', f"stderr (returncode={proc.returncode}): {proc.stderr.strip()}", stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
            else:
                app.app_trace_.record_warning('agent._run_once._run_once', Exception(f"stderr (returncode={proc.returncode}): {proc.stderr.strip()}"), stdout=proc.stdout, stderr=proc.stderr, returncode=proc.returncode)
        return Status.from_returncode(proc.returncode)
    except subprocess.TimeoutExpired as exc:
        partial_out = exc.output or ""
        partial_err = exc.stderr or f"Timeout after {timeout}s"
        app.app_trace_.record_warning_and_raise('agent._run_once._run_once', exc, stdout=partial_out, stderr=partial_err)
    except OSError as exc:
        app.app_trace_.record_error_and_raise('agent._run_once._run_once', exc)
    except Exception as exc:  # noqa: BLE001
        app.app_trace_.record_warning_and_raise('agent._run_once._run_once', exc)
