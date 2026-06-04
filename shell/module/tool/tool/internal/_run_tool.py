from __future__ import annotations

import subprocess

from shell.component.process.process.process import Process
from shell.status.status import Status


def _run_tool(tool, runner=None) -> Status:
    app = tool._app
    process = Process(app, runner)
    process.init_process_tool()
    try:
        process.run_process()
        app.app_trace_.record_info(
            'tool._run_tool._run_tool',
            f'returncode={process.returncode_}',
            stdout=process.stdout_,
            stderr=process.stderr_,
            returncode=process.returncode_,
        )
        if process.stderr_:
            app.app_trace_.record_warning(
                'tool._run_tool._run_tool',
                Exception(f"stderr (returncode={process.returncode_}): {process.stderr_.strip()}"),
                stdout=process.stdout_,
                stderr=process.stderr_,
                returncode=process.returncode_,
            )
        return Status.from_returncode(process.returncode_)
    except subprocess.TimeoutExpired:
        return Status.from_returncode(2)
    except Exception as exc:
        app.app_trace_.record_error('tool._run_tool._run_tool', exc)
        return Status.from_returncode(1)
