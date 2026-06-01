from __future__ import annotations

import yaml

from shell.component.message.message.message import Message
from shell.component.message.message_envelope.message_envelope import MessageEnvelope
from shell.component.message.source_type.source_type import SourceType


def _read_message_file(reader: object) -> Message:
    raw = reader.path_.read_text(encoding="utf-8")
    data = yaml.safe_load(raw)

    envelope = MessageEnvelope()
    envelope.init_envelope_data(data)

    message = Message()
    message._message_envelope = envelope
    message._source_name = str(reader.path_)
    message._source_type = SourceType.FILE

    return message
