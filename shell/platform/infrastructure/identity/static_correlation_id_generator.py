"""StaticCorrelationIdGenerator — adapter CorrelationIdGenerator dla testów i determinizmu."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


class StaticCorrelationIdGenerator:
    """Adapter — zwraca wartości z deterministycznej sekwencji.

    Służy do testowania (przewidywalne identyfikatory) oraz do kontekstów,
    w których identyfikatory korelacji muszą być stabilne w obrębie procesu.
    """

    def __init__(self, prefix: str = "corr-", *, sequence: Iterator[str] | None = None) -> None:
        self._prefix = prefix
        self._counter = 0
        self._sequence = sequence

    def generate(self) -> str:
        if self._sequence is not None:
            return next(self._sequence)
        value = f"{self._prefix}{self._counter}"
        self._counter += 1
        return value
