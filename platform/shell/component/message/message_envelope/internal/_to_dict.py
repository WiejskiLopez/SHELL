from __future__ import annotations


def _to_dict(envelope: object) -> dict:
    return {
        "meta": envelope.message_meta_.to_dict(),
        "payload": envelope.payload_,
    }
