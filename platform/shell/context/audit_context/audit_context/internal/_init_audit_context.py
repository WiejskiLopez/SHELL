from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.context.audit_context.audit_context.audit_context import AuditContext


def _init_audit_context(audit_context: AuditContext) -> None:
    audit_context._request_id = ""
    audit_context._user = ""
    audit_context._timestamp = ""
    audit_context._trace_id = ""
