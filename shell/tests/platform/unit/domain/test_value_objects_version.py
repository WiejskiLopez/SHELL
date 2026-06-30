"""Unit tests for Version value object."""

from __future__ import annotations

import pytest

from shell.domain.platform.value_objects.version import Version


class TestVersion:
    def test_initial_returns_version_one(self) -> None:
        assert Version.initial() == Version(1)

    def test_next_increments_value(self) -> None:
        v = Version(3)
        assert v.next() == Version(4)

    def test_next_does_not_mutate_original(self) -> None:
        v = Version(2)
        v.next()
        assert v == Version(2)

    def test_str_representation(self) -> None:
        assert str(Version(7)) == "7"

    def test_equality(self) -> None:
        assert Version(5) == Version(5)
        assert Version(5) != Version(6)

    def test_is_hashable(self) -> None:
        s = {Version(1), Version(1), Version(2)}
        assert s == {Version(1), Version(2)}

    @pytest.mark.parametrize("invalid", [0, -1, -100])
    def test_value_below_one_is_rejected(self, invalid: int) -> None:
        with pytest.raises(ValueError, match="Version must be >= 1"):
            Version(invalid)

    def test_is_frozen(self) -> None:
        v = Version(1)
        with pytest.raises((AttributeError, Exception)):
            v.value = 99  # type: ignore[misc]
