from __future__ import annotations

from dataclasses import dataclass

from shell.platform.infrastructure.serialization.command_registry import (
    build_command_registry,
)


@dataclass(frozen=True)
class ExampleCommand:
    value: str


@dataclass(frozen=True)
class OtherCommand:
    value: int


def test_build_command_registry_is_keyed_by_command_class_name() -> None:
    registry = build_command_registry((ExampleCommand, OtherCommand))

    assert registry == {
        "ExampleCommand": ExampleCommand,
        "OtherCommand": OtherCommand,
    }
