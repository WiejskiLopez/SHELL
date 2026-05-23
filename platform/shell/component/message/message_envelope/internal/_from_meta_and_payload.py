from __future__ import annotations


def _from_meta_and_payload(message_meta: object, payload: str) -> object:
    from shell.component.message.message_envelope.message_envelope import MessageEnvelope

    envelope = MessageEnvelope()
    envelope._message_meta = message_meta
    envelope._payload = payload
    return envelope
