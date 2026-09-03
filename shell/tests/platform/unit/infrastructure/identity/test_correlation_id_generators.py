from __future__ import annotations

from shell.platform.infrastructure.identity.static_correlation_id_generator import (
    StaticCorrelationIdGenerator,
)
from shell.platform.infrastructure.identity.uuid_correlation_id_generator import (
    UuidCorrelationIdGenerator,
)


class TestUuidCorrelationIdGenerator:
    def test_generates_distinct_uuid_strings(self) -> None:
        generator = UuidCorrelationIdGenerator()
        first = generator.generate()
        second = generator.generate()
        assert isinstance(first, str)
        assert first != second


class TestStaticCorrelationIdGenerator:
    def test_generates_deterministic_sequence(self) -> None:
        generator = StaticCorrelationIdGenerator(prefix="corr-")
        assert generator.generate() == "corr-0"
        assert generator.generate() == "corr-1"

    def test_uses_explicit_sequence(self) -> None:
        generator = StaticCorrelationIdGenerator(sequence=iter(("a", "b")))
        assert generator.generate() == "a"
        assert generator.generate() == "b"
