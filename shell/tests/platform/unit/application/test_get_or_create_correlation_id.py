from __future__ import annotations

from shell.platform.application.context.correlation_id import (
    get_or_create_correlation_id,
    reset_correlation_id,
    set_correlation_id,
    set_correlation_id_generator,
)
from shell.platform.infrastructure.identity.static_correlation_id_generator import (
    StaticCorrelationIdGenerator,
)


class TestGetOrCreateCorrelationId:
    def test_returns_existing_value(self) -> None:
        token = set_correlation_id("abc-123")
        try:
            assert get_or_create_correlation_id() == "abc-123"
        finally:
            reset_correlation_id(token)

    def test_generates_and_sets_when_empty(self) -> None:
        set_correlation_id_generator(StaticCorrelationIdGenerator(prefix="gen-"))
        token = set_correlation_id("")
        try:
            value = get_or_create_correlation_id()
            assert value == "gen-0"
            # wartość zostaje ustawiona w kontekście — ponowny odczyt nie generuje nowej
            assert get_or_create_correlation_id() == "gen-0"
        finally:
            reset_correlation_id(token)

    def test_never_returns_empty_string(self) -> None:
        set_correlation_id_generator(StaticCorrelationIdGenerator(prefix="g-"))
        token = set_correlation_id("")
        try:
            for _ in range(5):
                assert get_or_create_correlation_id()
        finally:
            reset_correlation_id(token)
