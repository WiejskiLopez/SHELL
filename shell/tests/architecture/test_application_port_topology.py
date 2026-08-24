"""Koncept: koherentna topologia application ports.

Reguła: kazdy port application nalezy do jednej grupy odpowiedzialnosci, a
stare plaskie moduly nie sa uzywane jako ukryty agregator.

Poprawnie: grupy messaging, persistence, transport i runtime istnieja, ich
stare pliki nie istnieja, a callerzy nie importuja starych sciezek.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PORTS = ROOT / "platform" / "application" / "ports"


def test_application_ports_have_canonical_grouped_topology() -> None:
    expected_paths = (
        PORTS / "messaging" / "event_publisher.py",
        PORTS / "persistence" / "unit_of_work.py",
        PORTS / "transport" / "delivery_transport.py",
        PORTS / "transport" / "delivery_dedup_store.py",
        PORTS / "runtime" / "readiness.py",
        PORTS / "runtime" / "metrics.py",
        PORTS / "runtime" / "seed.py",
        PORTS / "runtime" / "filesystem.py",
        PORTS / "logger.py",
        PORTS / "config.py",
    )
    old_paths = (
        PORTS / "messaging.py",
        PORTS / "unit_of_work.py",
        PORTS / "delivery_transport.py",
        PORTS / "delivery_dedup_store.py",
        PORTS / "readiness.py",
        PORTS / "metrics.py",
        PORTS / "seed.py",
        PORTS / "filesystem.py",
    )

    assert all(path.exists() for path in expected_paths)
    assert all(not path.exists() for path in old_paths)

    old_imports = (
        "application.ports." + "messaging import",
        "application.ports." + "unit_of_work import",
        "application.ports." + "delivery_transport import",
        "application.ports." + "delivery_dedup_store import",
        "application.ports." + "readiness import",
        "application.ports." + "metrics import",
        "application.ports." + "seed import",
        "application.ports." + "filesystem import",
    )
    for source in ROOT.rglob("*.py"):
        content = source.read_text(encoding="utf-8")
        assert not any(old_import in content for old_import in old_imports), source
