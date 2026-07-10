from __future__ import annotations

import pytest

from shell.platform.domain.value_objects.hash import Hash


class TestHash:
    def test_of_string(self) -> None:
        h = Hash.of("hello")
        assert len(h.value) == 64

    def test_deterministic(self) -> None:
        assert Hash.of("abc") == Hash.of("abc")

    def test_different_inputs(self) -> None:
        assert Hash.of("abc") != Hash.of("xyz")

    def test_invalid_length(self) -> None:
        with pytest.raises(ValueError):
            Hash("short")

    def test_invalid_hex(self) -> None:
        with pytest.raises(ValueError):
            Hash("z" * 64)
