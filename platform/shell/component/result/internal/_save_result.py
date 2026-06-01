"""_save_result.py
Responsible for one thing: persisting the graph result to .node/result/.

Files written:
    .node/result/stdout.md   — subprocess stdout (only when non-empty)
    .node/result/stderr.md   — subprocess stderr (only when non-empty)
    .node/result/result.yaml — returncode, start_time, stop_time (ISO format)
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from shell.utils.path.path import Path, PathType

if TYPE_CHECKING:
    from shell.app.app_trace.app_trace import AppTrace
    from shell.component.result.result import Result

_RESULT_DIR = Path.new(".node") / "result"
_STDOUT_FILE = _RESULT_DIR / "stdout.md"
_STDERR_FILE = _RESULT_DIR / "stderr.md"
_RESULT_YAML = _RESULT_DIR / "result.yaml"


def _save_result(node: PathType, result: 'Result', start_dt: datetime | None = None, stop_dt: datetime | None = None, trace: 'AppTrace | None' = None) -> None:
    """Write stdout, stderr and result.yaml into <node>/.node/result/.

    stdout.md and stderr.md are only written when content is non-empty.
    result.yaml is always written.
    """
    result_dir = node / _RESULT_DIR
    Path.mkdir(result_dir)
    if trace is not None:
        trace.record_info('result._save_result._save_result', f'mkdir {result_dir}')

    if result._stdout and result._stdout.strip():
        stdout_path = node / _STDOUT_FILE
        Path.write_text(stdout_path, result._stdout)
        if trace is not None:
            trace.record_info('result._save_result._save_result', f'write {stdout_path}')

    if result._stderr and result._stderr.strip():
        stderr_path = node / _STDERR_FILE
        Path.write_text(stderr_path, result._stderr)
        if trace is not None:
            trace.record_info('result._save_result._save_result', f'write {stderr_path}')

    returncode = int(result._status) if result._status is not None else 1
    start_iso = start_dt.isoformat() if start_dt is not None else None
    stop_iso = stop_dt.isoformat() if stop_dt is not None else None

    yaml_content = (
        f"returncode: {returncode}\n"
        f"start_time: {start_iso}\n"
        f"stop_time: {stop_iso}\n"
    )
    result_yaml_path = node / _RESULT_YAML
    Path.write_text(result_yaml_path, yaml_content)
    if trace is not None:
        trace.record_info('result._save_result._save_result', f'write {result_yaml_path}')
