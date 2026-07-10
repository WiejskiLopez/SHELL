from __future__ import annotations

from contextvars import ContextVar, Token

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


def get_correlation_id() -> str:
    return correlation_id_var.get()


def set_correlation_id(value: str) -> Token[str]:
    return correlation_id_var.set(value)


def reset_correlation_id(token: Token[str]) -> None:
    correlation_id_var.reset(token)
