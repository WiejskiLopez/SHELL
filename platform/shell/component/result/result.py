"""result.py
Result — singleton execution result for a single shell graph run.

Klasa `Result` jest tworzona raz na uruchomienie i aktualizowana
w miejscach, gdzie runner kończy pracę lub subproces zwraca wynik.

__slots__:
    _app  — referencja do App (DOM back-reference)
    status          — semantyczny wynik z perspektywy graph
                      ('success', 'error', 'timeout', 'warning', 'locked',
                       'question', 'waiting', 'skip', 'critical')
    stdout          — standardowe wyjście subprocesu
    stderr          — wyjście błędów subprocesu
    returncode      — niskopoziomowy kod wyjścia subprocesu (int | None)
    returncode_     — property: returncode lub CRITICAL(10) gdy slot jest None

Rozróżnienie status vs returncode:
    returncode — techniczny wynik subprocesu (0 = sukces, inne = błąd)
    status     — semantyczny wynik graph (returncode=0 może dać status=waiting)
"""

from __future__ import annotations

from shell.utils.path.path import Path, PathType
from typing import TYPE_CHECKING

from shell.component.result.internal._save_result import _save_result
from shell.status.status import Status

if TYPE_CHECKING:
    from shell.app.app.app import App
    from shell.app.app_trace.app_trace import AppTrace


class Result:
    """Singleton execution result for a single graph run."""

    Status = Status

    _TERMINAL_STATUSES: frozenset = frozenset({Status.ERROR, Status.LOCKED, Status.CRITICAL})

    __slots__ = (
        "_app",
        "_status",
        "_stdout",
        "_stderr",
        "_returncode",
    )

    def __init__(self, app: 'App | None' = None) -> None:
        self._app: App | None = app
        self._status: Status = Status.NULL
        self._stdout: str | None = None
        self._stderr: str | None = None
        self._returncode: int | None = None

    # -----------------------------------------------------------------------
    # Factory
    # -----------------------------------------------------------------------

    @classmethod
    def from_trace(cls, trace: 'AppTrace', app: 'App | None' = None) -> 'Result':
        """Construct a Result from a completed AppTrace.

        Status resolution priority:
          1. any error event  → ERROR,  returncode=1
          2. any warning event → WARNING, returncode=2
          3. otherwise        → SUCCESS, returncode=0
        """
        result = cls(app)
        result._stdout = trace.stdout_
        result._stderr = trace.stderr_
        result._returncode = trace.returncode_
        if trace.has_errors_:
            result._status = Status.ERROR
        elif trace.has_warnings_:
            result._status = Status.WARNING
        else:
            result._status = Status.SUCCESS
        return result

    # -----------------------------------------------------------------------
    # Status predicates
    # -----------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"Result(status={self._status!r}, returncode={self._returncode!r})"

    @property
    def status_(self) -> Status:
        """Return current graph status."""
        return self._status

    @property
    def stdout_(self) -> str | None:
        """Return subprocess stdout."""
        return self._stdout

    @property
    def stderr_(self) -> str | None:
        """Return subprocess stderr."""
        return self._stderr

    @property
    def returncode_(self) -> int:
        """Return returncode or CRITICAL (10) when slot is None.

        None means the process never started — treated as critical failure.
        """
        if self._returncode is None:
            return Status.CRITICAL
        return self._returncode

    @property
    def is_terminal_(self) -> bool:
        """Return True when status is a terminal (non-retryable) value."""
        return self._status in self._TERMINAL_STATUSES

    @property
    def is_success_(self) -> bool:
        return self._status == Status.SUCCESS

    @property
    def is_error_(self) -> bool:
        return self._status == Status.ERROR

    # -----------------------------------------------------------------------
    # Save result
    # -----------------------------------------------------------------------

    def save_result(self) -> None:
        """Persist stdout, stderr and result.yaml to <node>/.node/result/.

        Node path is resolved from the back-reference to app.
        """
        try:
            node = Path.new(self._app.app_node_.node_.node_dir_)
            start_dt = self._app.app_trace_._start_trace_date_time
            stop_dt = self._app.app_trace_._stop_trace_date_time
            _save_result(node, self, start_dt, stop_dt, self._app.app_trace_)
        except Exception as exc:
            self._app.app_trace_.record_error('result.Result.save_result', exc)

    # -----------------------------------------------------------------------
    # Runner result
    # -----------------------------------------------------------------------

    @property
    def runner_result_(self) -> dict:
        """Return a serialisable execution summary dict.

        Keys: timestamp, status, role, mode, version, start, stop.
        start/stop are ISO-format UTC strings from AppTrace.
        Reads role, mode and version from app when available.
        """
        from datetime import datetime, timezone
        role = self._app.app_properties_.role_
        mode = self._app.runner_.mode_
        manifest_version = self._app.manifest_.manifest_version_
        start_dt = self._app.app_trace_._start_trace_date_time
        stop_dt = self._app.app_trace_._stop_trace_date_time
        return {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': self._status if self._status is not None else 'unknown',
            'role': role,
            'mode': mode,
            'version': manifest_version,
            'start': start_dt.isoformat() if start_dt is not None else None,
            'stop': stop_dt.isoformat() if stop_dt is not None else None,
        }


