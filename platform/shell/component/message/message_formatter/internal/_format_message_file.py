from __future__ import annotations

import yaml

from shell.component.message.message.message import Message
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
from shell.component.message.message_formatter.internal._assert_message_meta_set import _assert_message_meta_set
from shell.component.message.message_meta.message_meta import MessageMeta
from shell.component.message.message_reader.message_reader import MessageReader
from shell.component.message.source_type.source_type import SourceType
from shell.utils.path.path import Path


def _format_message_file(formatter: object, message_meta: MessageMeta | None) -> Message:
    path = formatter.path_
    raw = Path.read_text(path)

    is_message_file = False
    try:
        data = yaml.safe_load(raw)
        if isinstance(data, dict) and "meta" in data and "payload" in data:
            is_message_file = True
    except Exception:
        pass

    if is_message_file:
        reader = MessageReader()
        reader._path = path
        return reader.read_message_file()

    _assert_message_meta_set(message_meta)

    envelope = MessageEnvelope.from_meta_and_payload(message_meta, raw)

    return Message.from_envelope(envelope, str(path), SourceType.FILE)
