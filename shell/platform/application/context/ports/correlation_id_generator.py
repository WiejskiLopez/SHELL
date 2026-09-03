"""CorrelationIdGenerator port — dostarcza identyfikator korelacji dla tracingu."""

from __future__ import annotations

from typing import Protocol


class CorrelationIdGenerator(Protocol):
    """Port — generuje nowy, unikalny identyfikator korelacji.

    Pozwala podmienić backend generowania (UUID, ULID, generator z zaplecza
    distributed tracing) bez zmiany konsumentów. Identyfikator jest używany
    jako źródło ``correlation_id`` na granicy wejścia kontekstu wykonania,
    gdy żaden identyfikator nie został dostarczony z zewnątrz (brak nagłówka,
    wywołanie spoza HTTP itp.).
    """

    def generate(self) -> str: ...
