from __future__ import annotations


def _init_process_command(process_command: 'ProcessCommand', cmd: list[str], cwd: str, stdin: str | None = None, timeout: int | None = None, env: dict | None = None) -> None:
    process_command._cmd = cmd
    process_command._stdin = stdin
    process_command._timeout = timeout
    process_command._cwd = cwd
    process_command._env = env
    if process_command._cmd is None:
        raise ValueError("ProcessCommand._cmd is required")
    if process_command._cwd is None:
        raise ValueError("ProcessCommand._cwd is required")
