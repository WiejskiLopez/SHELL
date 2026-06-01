from __future__ import annotations


def _from_envelope(envelope: object, source_name: str, source_type: object) -> object:
    from shell.component.message.message.message import Message
    from shell.component.message.message_status.message_status import MessageStatus

    message = Message()
    message._message_envelope = envelope
    message._source_name = source_name
    message._source_type = source_type
    message._status = MessageStatus.CREATED
    return message
