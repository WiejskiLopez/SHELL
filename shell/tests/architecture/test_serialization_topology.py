"""Koncept: jedna kanoniczna topologia serializacji platformy.

Reguła: serializer, deserializer i registry sa pogrupowane wedlug rodzaju
kontraktu, bez pozostawionych starych sciezek implementation.

Poprawnie: event, message, command i registries maja canonical paths, a callerzy
nie importuja usunietych modulow.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SERIALIZATION = ROOT / "platform" / "infrastructure" / "serialization"


def test_serialization_has_canonical_grouped_topology() -> None:
    expected = (
        SERIALIZATION / "integration_event" / "integration_event_deserializer.py",
        SERIALIZATION / "integration_event" / "integration_event_serializer.py",
        SERIALIZATION / "command" / "deserializer.py",
        SERIALIZATION / "payload" / "payload_object_deserializer.py",
        SERIALIZATION / "payload" / "payload_type_hints_resolver.py",
        SERIALIZATION / "payload" / "payload_value_deserializer.py",
        SERIALIZATION / "payload" / "payload_value_serializer.py",
        SERIALIZATION / "registries" / "type_registry.py",
        SERIALIZATION / "registries" / "event_registry.py",
        SERIALIZATION / "registries" / "command_registry.py",
        SERIALIZATION / "upcaster.py",
    )
    old_paths = (
        SERIALIZATION / "event",
        SERIALIZATION / "envelope",
        SERIALIZATION / "event" / "domain_event_serializer.py",
        SERIALIZATION / "event" / "event_deserializer.py",
        SERIALIZATION / "event" / "event_envelope_serializer.py",
        SERIALIZATION / "event" / "serializer.py",
        SERIALIZATION / "event" / "deserializer.py",
        SERIALIZATION / "envelope" / "envelope_engine.py",
        SERIALIZATION / "uow_serializer.py",
        SERIALIZATION / "message" / "serializer.py",
        SERIALIZATION / "message" / "deserializer.py",
        SERIALIZATION / "event_serializer.py",
        SERIALIZATION / "event_deserializer.py",
        SERIALIZATION / "message_serializer.py",
        SERIALIZATION / "message_deserializer.py",
        SERIALIZATION / "type_registry.py",
        SERIALIZATION / "event_registry.py",
        SERIALIZATION / "message_registry.py",
        SERIALIZATION / "command_registry.py",
        ROOT
        / "platform"
        / "infrastructure"
        / "messaging"
        / "serialization"
        / "command_deserializer.py",
    )

    assert all(path.exists() for path in expected)
    assert all(not path.exists() for path in old_paths)

    old_imports = (
        "infrastructure.serialization." + "event_serializer",
        "infrastructure.serialization." + "event_deserializer",
        "infrastructure.serialization." + "message_serializer",
        "infrastructure.serialization." + "message_deserializer",
        "infrastructure.serialization." + "type_registry",
        "infrastructure.serialization." + "event_registry",
        "infrastructure.serialization." + "message_registry",
        "infrastructure.serialization." + "command_registry",
        "infrastructure.messaging.serialization." + "command_deserializer",
        "infrastructure.serialization." + "event.",
        "infrastructure.serialization." + "envelope.",
        "infrastructure.serialization." + "uow_serializer",
    )
    for source in ROOT.rglob("*.py"):
        content = source.read_text(encoding="utf-8")
        assert not any(old_import in content for old_import in old_imports), source
