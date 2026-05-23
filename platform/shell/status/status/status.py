"""status.py
Status — semantic result of a graph run.

Values match OS exit codes:
    SUCCESS  = 0
    ERROR    = 1
    TIMEOUT  = 2
    WARNING  = 3
    LOCKED   = 4
    QUESTION = 5
    WAITING  = 6
    SKIP     = 7
    READY        = 8
    INITIALIZED  = 9
    NULL         = 10
    DONE         = 11
    CRITICAL = 99
"""

from __future__ import annotations

from enum import Enum


class Status(int, Enum):
    SUCCESS = 0
    ERROR = 1
    TIMEOUT = 2
    WARNING = 3
    LOCKED = 4
    QUESTION = 5
    WAITING = 6
    SKIP = 7
    READY = 8
    INITIALIZED = 9
    NULL = 10
    DONE = 11
    CRITICAL = 99

    @classmethod
    def from_returncode(cls, returncode: int) -> 'Status':
        try:
            return cls(returncode)
        except ValueError:
            return cls.ERROR

    @classmethod
    def from_str(cls, value: str) -> 'Status':
        try:
            return cls[value.upper()]
        except KeyError:
            raise ValueError(f"[Status] Unknown status value: '{value}'")
