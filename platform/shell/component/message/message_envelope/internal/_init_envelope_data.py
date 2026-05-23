from __future__ import annotations

from shell.component.message.message_envelope.internal._assert_envelope_fields import _assert_envelope_fields
from shell.component.message.message_meta.message_meta import MessageMeta


def _init_envelope_data(envelope: object, data: dict) -> None:
    _assert_envelope_fields(data)

    meta = MessageMeta()
    meta.init_meta_data(data.get("meta", {}))
    envelope._message_meta = meta
    envelope._payload = data.get("payload")
