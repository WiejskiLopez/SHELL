"""event.py
Event — single execution event collected by AppTrace.

Slots:
    _log_level_code — event type: 'error' | 'warning' | 'success' | 'info'
    _event_type     — EventType.SAVE | EventType.NOT_SAVE; NOT_SAVE events are not written to archive
    _source     — origin label (e.g. 'run_runner', 'init_app')
    _message    — human-readable description
    _timestamp  — UTC datetime of event creation
    _stdout     — Optional; raw stdout
    _stderr     — Optional; raw stderr
    _returncode — Optional; process exit code
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum


class EventType(Enum):
    SAVE = 'save'
    NOT_SAVE = 'not_save'


class Event:
    """Single execution event collected during a graph run."""

    __slots__ = ("_log_level_code", "_event_type", "_source", "_message", "_timestamp", "_stdout", "_stderr", "_returncode")

    def __init__(self) -> None:
        self._log_level_code: str | None = None
        self._event_type: EventType = EventType.SAVE
        self._source: str | None = None
        self._message: str | None = None
        self._timestamp: datetime | None = None
        self._stdout: str | None = None
        self._stderr: str | None = None
        self._returncode: int | None = None

    @property
    def log_level_code_(self) -> str | None:
        return self._log_level_code

    @property
    def event_type_(self) -> EventType:
        return self._event_type

    @property
    def source_(self) -> str | None:
        return self._source

    @property
    def message_(self) -> str | None:
        return self._message

    @property
    def timestamp_iso_(self) -> str | None:
        if self._timestamp is None:
            return None
        return self._timestamp.isoformat(timespec='milliseconds').replace('+00:00', 'Z')

    @property
    def stdout_(self) -> str | None:
        return self._stdout

    @property
    def stderr_(self) -> str | None:
        return self._stderr

    @property
    def returncode_(self) -> int | None:
        return self._returncode

    @property
    def formatted_event_line_(self) -> str:
        errorcode = self._returncode if self._returncode is not None else '-'
        return f"{self.timestamp_iso_} | {self._source} | {errorcode} | {self._message}"
