"""node_status.py
NodeStatus — owns and manages the status of a single node.

Slots:
    _status — current Status value (Status | None)

Validated properties:
    status_ — returns current status value

Methods:
    set_status(value) — set status from Status or int
"""

from __future__ import annotations

from shell.status.status import Status


class NodeStatus:
    """Owns and manages the status of a single node."""

    __slots__ = ("_app", "_status")

    def __init__(self, status: Status | int | None = None) -> None:
        self._app = None
        self._status: Status | None = None
        if status is not None:
            self.set_status(status)

    @property
    def status_(self) -> Status | None:
        """Return current status value."""
        return self._status

    @property
    def is_ready_(self) -> bool:
        """Return True when status is READY."""
        return self._status == Status.READY

    def set_status(self, value: Status | int) -> None:
        """Set status from Status enum or int exit code."""
        if isinstance(value, Status):
            self._status = value
        else:
            self._status = Status(value)

    def init_status(self, status_str: str | None) -> None:
        if status_str is None:
            self._status = Status.NULL
        else:
            self._status = Status.from_str(status_str)
