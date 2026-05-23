from __future__ import annotations

from enum import Enum


class MessageType(str, Enum):
    EVENT = "event"
    COMMAND = "command"
    REQUEST = "request"
    RESPONSE = "response"
    ACK = "ack"
    EXECUTED = "executed"
    OK = "ok"
    TASK = "task"
    DONE = "done"
