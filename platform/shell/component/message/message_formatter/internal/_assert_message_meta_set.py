from __future__ import annotations


def _assert_message_meta_set(message_meta) -> None:
    if message_meta is None:
        raise ValueError("[MessageFormatter] message_meta is required for plain text files")
