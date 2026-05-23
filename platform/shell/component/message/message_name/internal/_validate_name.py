from __future__ import annotations

from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_name.internal._format_name import _format_name


def _validate_name(name: str, meta: MessageMeta) -> bool:
    return name == _format_name(meta)
