from __future__ import annotations

from shell.utils.path.path import Path, PathType
from dataclasses import dataclass

SEPARATOR = '__'
FROM_PLACEHOLDER = 'X'


@dataclass
class MessageFilename:
    sequence_id: str
    from_role: str
    to_role: str
    msg_type: str
    intent: str
    thread_id: str
    message_id: str
    step: str
    suffix: str


def parse_message_filename(filename: str) -> MessageFilename | None:
    path = Path.new(filename)
    parts = path.stem.split(SEPARATOR)
    if len(parts) != 8:
        return None
    return MessageFilename(
        sequence_id=parts[0],
        from_role=parts[1],
        to_role=parts[2],
        msg_type=parts[3],
        intent=parts[4],
        thread_id=parts[5],
        message_id=parts[6],
        step=parts[7],
        suffix=path.suffix,
    )


def build_message_filename(parsed: MessageFilename, from_role: str) -> str:
    return SEPARATOR.join([
        parsed.sequence_id,
        from_role,
        parsed.to_role,
        parsed.msg_type,
        parsed.intent,
        parsed.thread_id,
        parsed.message_id,
        parsed.step,
    ]) + parsed.suffix


def increment_step(parsed: MessageFilename) -> str:
    try:
        new_step = str(int(parsed.step) + 1)
    except ValueError:
        new_step = parsed.step
    return SEPARATOR.join([
        parsed.sequence_id,
        parsed.from_role,
        parsed.to_role,
        parsed.msg_type,
        parsed.intent,
        parsed.thread_id,
        parsed.message_id,
        new_step,
    ]) + parsed.suffix
