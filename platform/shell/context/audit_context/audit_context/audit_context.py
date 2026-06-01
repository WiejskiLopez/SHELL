"""audit_context.py
AuditContext — audit and traceability context for process reconstruction.

Slots:
    _request_id — unique request identifier
    _user       — user or agent that initiated the request
    _timestamp  — ISO 8601 timestamp of the request
    _trace_id   — distributed trace identifier
"""

from __future__ import annotations

from shell.context.audit_context.audit_context.internal._init_audit_context import _init_audit_context


class AuditContext:
    """Audit and traceability context.

    Slots:
        _request_id — unique request identifier
        _user       — user or agent that initiated the request
        _timestamp  — ISO 8601 timestamp of the request
        _trace_id   — distributed trace identifier
    """

    __slots__ = ("_request_id", "_user", "_timestamp", "_trace_id")

    def __init__(self) -> None:
        self._request_id: str = ""
        self._user: str = ""
        self._timestamp: str = ""
        self._trace_id: str = ""

    @property
    def request_id_(self) -> str:
        return self._request_id

    @property
    def user_(self) -> str:
        return self._user

    @property
    def timestamp_(self) -> str:
        return self._timestamp

    @property
    def trace_id_(self) -> str:
        return self._trace_id

    def init_audit_context(self) -> None:
        _init_audit_context(self)
