from __future__ import annotations


def _assert_envelope_fields(data: dict) -> None:
    if "meta" not in data:
        raise ValueError("[MessageEnvelope] missing required section 'meta'")
    if "payload" not in data:
        raise ValueError("[MessageEnvelope] missing required field 'payload'")
