"""DeliveryColumnsMixin — wspólne kolumny techniczne tabel delivery.

Kolumny korelacji i payloadu są wspólne dla wszystkich tabel outbox/inbox
(event i command). Mixin usuwa ich duplikację w modelach delivery
(`event_delivery.py`, `command_delivery.py`). Kolumny stanu inbox
(status/lease/retry) pozostają w `InboxStateMixin` (persistence), a kolumna
`schema_version` jest wspólna dla obu (w inboxach dostarcza ją `InboxStateMixin`).
"""

from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column

from shell.platform.infrastructure.persistence.sql.models._compat import JSONB


class DeliveryColumnsMixin:
    """Techniczne kolumny wspólne dla tabel delivery (outbox i inbox)."""

    correlation_id: Mapped[str] = mapped_column(nullable=False, default="")
    causation_id: Mapped[str] = mapped_column(nullable=False, default="")
    payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)