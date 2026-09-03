"""Correlation ID — ambient tracing ContextVar API.

Przechowuje ``correlation_id`` jako ambientowy ``ContextVar`` i zapewnia
``get_or_create_correlation_id()`` — nigdy nie zwraca pustego identyfikatora.

Zasady warstwowe (Clean Architecture):
- moduł aplikacji ``application.context`` **nie może** importować infrastruktury;
- dlatego instancja generująca identyfikatory jest dostarczana przez port
  ``CorrelationIdGenerator`` i **ustawiana w Composition Root** przez
  ``set_correlation_id_generator``;
- jeżeli nie ustawiono generatora, używany jest wbudowany (wewnątrz aplikacji)
  fallback UUID — aby ``get_or_create_correlation_id`` nigdy nie zwrócił ``""``.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar, Token
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.platform.application.context.ports.correlation_id_generator import (
        CorrelationIdGenerator,
    )

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class _UuidFallbackGenerator:
    """Wbudowany fallback — generuje UUID4 bez zależności od infrastruktury."""

    def generate(self) -> str:
        return str(uuid.uuid4())


_generator: CorrelationIdGenerator = _UuidFallbackGenerator()


def set_correlation_id_generator(generator: CorrelationIdGenerator) -> None:
    """Ustawia generator identyfikatorów korelacji (wywoływane w Composition Root).

    Główny punkt wymiany backendu tracingu (UUID, ULID, backend distributed
    tracing). Przyjmuje dowolny obiekt spełniający ``CorrelationIdGenerator``.
    """
    _replace_generator(generator)


def _replace_generator(generator: CorrelationIdGenerator) -> None:
    global _generator
    _generator = generator


def get_correlation_id() -> str:
    return correlation_id_var.get()


def get_or_create_correlation_id() -> str:
    """Zwraca bieżący ``correlation_id``, generując i ustawiając nowy, gdy pusty.

    Używany tam, gdzie zapisujemy lub logujemy trace bez pośrednictwa granicy
    wejścia (HTTP middleware / worker / CLI): zapewnia, że outbox, komendy i
    rekordy audytowe nigdy nie trafią do systemu z pustym identyfikatorem.
    """
    value = correlation_id_var.get()
    if value:
        return value
    value = _generator.generate()
    correlation_id_var.set(value)
    return value


def set_correlation_id(value: str) -> Token[str]:
    return correlation_id_var.set(value)


def reset_correlation_id(token: Token[str]) -> None:
    correlation_id_var.reset(token)
