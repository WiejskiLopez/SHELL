from __future__ import annotations

import os


def _run_process(process: 'Process', cwd: str) -> None:
    command = process.process_command_.command_
    try:
        completed = process._runner(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            env={**os.environ, 'PYTHONUTF8': '1'},
            cwd=cwd,
        )
        process._returncode = completed.returncode
        process._stdout = completed.stdout
        process._stderr = completed.stderr
    except Exception as exc:
        raise RuntimeError(f"[Process] failed to run command {cmd}: {exc}") from exc
