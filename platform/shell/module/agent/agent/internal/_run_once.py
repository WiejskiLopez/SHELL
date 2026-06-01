from __future__ import annotations

import subprocess

from shell.component.process.process.process import Process
from shell.status.status import Status


def _run_once(
    prompt: str,
    timeout: int,
    app,
    runner=None,
    which=None,
    os_name=None,
) -> Status:
    process = Process(app, runner)
    process.init_process_agent(prompt, timeout, which, os_name)
    try:
        process.run_process()
        app.app_trace_.record_info('agent._run_once._run_once', f'returncode={process.returncode_}', stdout=process.stdout_, stderr=process.stderr_, returncode=process.returncode_)
        if process.stdout_ and process.stdout_.strip():
            app.app_trace_.record_info('agent._run_once._run_once', f'stdout:\n{process.stdout_.strip()}', stdout=process.stdout_, returncode=process.returncode_)
        if process.stderr_:
            if process.returncode_ == 0:
                app.app_trace_.record_info('agent._run_once._run_once', f"stderr (returncode={process.returncode_}): {process.stderr_.strip()}", stdout=process.stdout_, stderr=process.stderr_, returncode=process.returncode_)
            else:
                app.app_trace_.record_warning('agent._run_once._run_once', Exception(f"stderr (returncode={process.returncode_}): {process.stderr_.strip()}"), stdout=process.stdout_, stderr=process.stderr_, returncode=process.returncode_)
        return Status.from_returncode(process.returncode_)
    except subprocess.TimeoutExpired as exc:
        partial_out = exc.output or ""
        partial_err = exc.stderr or f"Timeout after {timeout}s"
        app.app_trace_.record_warning_and_raise('agent._run_once._run_once', exc, stdout=partial_out, stderr=partial_err)
    except OSError as exc:
        app.app_trace_.record_error_and_raise('agent._run_once._run_once', exc)
    except Exception as exc:  # noqa: BLE001
        app.app_trace_.record_warning_and_raise('agent._run_once._run_once', exc)
