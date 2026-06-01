"""app_trace.py
AppTrace — collects execution events during a single shell graph run.

Accumulates events (error, warning, success, info) from all phases.
Result is constructed from the trace at the end via Result.from_trace().

Slots:
    _events                           — list of collected Event objects
    _logger                           — Logger instance (for internal logging within record methods)
    _start_trace_date_time            — Optional; UTC datetime set by start_trace() (millisecond precision)
    _stop_trace_date_time             — Optional; UTC datetime set by stop_trace() (millisecond precision)
    _app_trace_status                 — AppTraceStatus enum; controls file-logging behaviour

AppTraceStatus lifecycle:
    BEFORE_SAVE  — initial; events collected, NOT sent to file logger (node_dir not yet set)
    SAVE         — normal; events collected AND sent to file logger
    AFTER_SAVE   — post-summary; events collected for printing only, NOT sent to file logger
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Literal

from shell.app.app_trace.event.event import Event, EventType
from shell.logger.logger import Logger

if TYPE_CHECKING:
    pass

LogLevelCode = Literal['error', 'warning', 'success', 'info']


class AppTraceStatus(Enum):
    BEFORE_SAVE = 'before_save'
    SAVE = 'save'
    AFTER_SAVE = 'after_save'


class AppTrace:
    """Collects execution events for a single graph run."""

    __slots__ = ("_events", "_logger", "_start_trace_date_time", "_stop_trace_date_time", "_app_trace_status")

    def __init__(self, app) -> None:
        self._events: list[Event] = []
        self._logger = Logger(app)
        self._start_trace_date_time: datetime | None = None
        self._stop_trace_date_time: datetime | None = None
        self._app_trace_status: AppTraceStatus = AppTraceStatus.BEFORE_SAVE

    def start_trace(self) -> None:
        _now = datetime.now(timezone.utc)
        self._start_trace_date_time = _now.replace(microsecond=(_now.microsecond // 1000) * 1000)
        self.record_info('app_trace.AppTrace.start_trace', 'session started')

    def stop_trace(self) -> None:
        try:
            _now = datetime.now(timezone.utc)
            self._stop_trace_date_time = _now.replace(microsecond=(_now.microsecond // 1000) * 1000)
            self.record_info('app_trace.AppTrace.stop_trace', 'session stopped')
            self._app_trace_status = AppTraceStatus.AFTER_SAVE
        except Exception as exc:
            self.record_error('app_trace.AppTrace.stop_trace', exc)

    # -----------------------------------------------------------------------
    # Record methods
    # -----------------------------------------------------------------------

    def record_error(self, source: str, exc: Exception, stdout: str = '', stderr: str = '', returncode: int | None = None) -> None:
        """Record an error event."""
        message = str(exc)
        self._try_activate_save_mode()
        if self._app_trace_status != AppTraceStatus.BEFORE_SAVE:
            self._logger.error(f'[{source}] {message}', exc_info=True)
        self._append('error', source, message, stdout, stderr, returncode)

    def record_warning(self, source: str, exc: Exception, stdout: str = '', stderr: str = '', returncode: int | None = None) -> None:
        """Record a warning event."""
        message = str(exc)
        self._try_activate_save_mode()
        if self._app_trace_status != AppTraceStatus.BEFORE_SAVE:
            self._logger.warning(f'[{source}] {message}')
        self._append('warning', source, message, stdout, stderr, returncode)

    def record_error_and_raise(self, source: str, exc: Exception, stdout: str = '', stderr: str = '', returncode: int | None = None) -> None:
        """Record an error event then re-raise the exception."""
        self.record_error(source, exc, stdout, stderr, returncode)
        raise exc

    def record_warning_and_raise(self, source: str, exc: Exception, stdout: str = '', stderr: str = '', returncode: int | None = None) -> None:
        """Record a warning event then re-raise the exception."""
        self.record_warning(source, exc, stdout, stderr, returncode)
        raise exc

    def record_info(self, source: str, message: str, stdout: str = '', stderr: str = '', returncode: int | None = None, event_type: EventType = EventType.SAVE) -> None:
        """Record an informational event."""
        self._try_activate_save_mode()
        if self._app_trace_status != AppTraceStatus.BEFORE_SAVE:
            self._logger.info(f'[{source}] {message}')
        self._append('info', source, message, stdout, stderr, returncode, event_type)

    def record_info_not_save(self, source: str, message: str, stdout: str = '', stderr: str = '', returncode: int | None = None) -> None:
        """Record an informational event that is not written to archive."""
        self._try_activate_save_mode()
        if self._app_trace_status != AppTraceStatus.BEFORE_SAVE:
            self._logger.info(f'[{source}] {message}')
        self._append('info', source, message, stdout, stderr, returncode, EventType.NOT_SAVE)

    def record_summary(self) -> None:
        """Record a NOT_SAVE summary line built from internal trace state."""
        returncode = self.returncode_
        start = self._start_trace_date_time
        stop = self._stop_trace_date_time
        self.record_info_not_save(
            'app_trace.AppTrace.record_summary',
            f"returncode={returncode} start={start.isoformat() if start else None} stop={stop.isoformat() if stop else None}",
            returncode=returncode,
        )

    # -----------------------------------------------------------------------
    # Module facades
    # -----------------------------------------------------------------------

    @property
    def logger_(self) -> Logger:
        return self._logger

    # -----------------------------------------------------------------------
    # Aggregation helpers
    # -----------------------------------------------------------------------

    @property
    def events_(self) -> list[Event]:
        return list(self._events)

    @property
    def has_errors_(self) -> bool:
        return any(e.log_level_code_ == 'error' for e in self.events_)

    @property
    def has_done_(self) -> bool:
        return any(e.returncode_ == 11 for e in self.events_)

    @property
    def has_warnings_(self) -> bool:
        return any(e.log_level_code_ == 'warning' for e in self.events_)

    @property
    def stdout_(self) -> str:
        """Concatenate all success/info messages as stdout."""
        return "\n".join(
            e.formatted_event_line_ for e in self.events_ if e.log_level_code_ in ('success', 'info') and e.event_type_ == EventType.SAVE
        )

    @property
    def stderr_(self) -> str:
        """Concatenate all error/warning messages as stderr."""
        return "\n".join(
            e.formatted_event_line_ for e in self.events_ if e.log_level_code_ in ('error', 'warning') and e.event_type_ == EventType.SAVE
        )

    @property
    def not_save_lines_(self) -> str:
        """Concatenate all NOT_SAVE event lines for end-of-run printing only."""
        return "\n".join(
            e.formatted_event_line_ for e in self.events_ if e.event_type_ == EventType.NOT_SAVE
        )

    @property
    def returncode_(self) -> int:
        """Derive OS exit code from collected events."""
        if self.has_errors_:
            return 1
        if self.has_done_:
            return 11
        if self.has_warnings_:
            return 2
        return 0

    # -----------------------------------------------------------------------
    # Internal
    # -----------------------------------------------------------------------

    def _try_activate_save_mode(self) -> None:
        if self._app_trace_status != AppTraceStatus.BEFORE_SAVE:
            return
        try:
            self._logger._app.app_node_.node_.node_dir_
        except (ValueError, AttributeError):
            return
        self._app_trace_status = AppTraceStatus.SAVE
        buffered = list(self.events_)
        for event in buffered:
            self._flush_event_to_logger(event)

    def _flush_event_to_logger(self, event: Event) -> None:
        source = event._source
        message = event._message
        lc = event._log_level_code
        if lc in ('info', 'success'):
            self._logger.info(f'[{source}] {message}')
        elif lc == 'warning':
            self._logger.warning(f'[{source}] {message}')
        elif lc == 'error':
            self._logger.error(f'[{source}] {message}')

    def _append(
        self,
        log_level_code: LogLevelCode,
        source: str,
        message: str,
        stdout: str = '',
        stderr: str = '',
        returncode: int | None = None,
        event_type: EventType = EventType.SAVE,
    ) -> None:
        event = Event()
        event._log_level_code = log_level_code
        event._event_type = event_type
        event._source = source
        event._message = message
        event._timestamp = datetime.now(timezone.utc)
        event._stdout = stdout
        event._stderr = stderr
        event._returncode = returncode
        self._events.append(event)



