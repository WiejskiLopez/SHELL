from __future__ import annotations

from contextvars import ContextVar, Token

causation_id_var: ContextVar[str] = ContextVar("causation_id", default="")


def get_causation_id() -> str:
    return causation_id_var.get()


def set_causation_id(value: str) -> Token[str]:
    return causation_id_var.set(value)


def reset_causation_id(token: Token[str]) -> None:
    causation_id_var.reset(token)
