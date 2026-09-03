"""Koncept: reguła architektoniczna dotycząca regressions: only static per-table migrations.

Reguła: każda migracja (servisowa i platformowa) jest statyczna per tabela
(``op.create_table`` / ``op.drop_table`` / ``op.*``) i nie używa dynamicznych baseline'ów
z ORM metadata (``apply_baseline``, ``create_service_tables`` itd.). Legacy wzorzec jest
zabroniony — refaktor na statyczny wzorzec wykonuje się do końca, bez wyjątków.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files

_FORBIDDEN_DYNAMIC_SYMBOLS = (
    "apply_baseline",
    "revert_baseline",
    "apply_delivery_baseline",
    "revert_delivery_baseline",
    "create_service_tables",
    "drop_service_tables",
    "create_service_delivery_tables",
    "drop_service_delivery_tables",
)


def _migration_roots() -> list:
    roots = [
        BASE / service_root / "migrations" / "versions"
        for service_root in (BASE, *BASE.glob("*_service"))
    ]
    return [root for root in roots if root.is_dir()]


def test_migration_baselines_use_orm_metadata() -> None:
    violations: list[str] = []
    platform_versions = (
        BASE / "platform" / "infrastructure" / "persistence" / "migrations" / "sql" / "versions"
    )
    for migrations_dir in (*_migration_roots(), platform_versions):
        if not migrations_dir.is_dir():
            continue
        for path in iter_py_files(migrations_dir):
            rel = path.relative_to(BASE).as_posix()
            src = path.read_text(encoding="utf-8")
            if "op." not in src:
                violations.append(
                    f"{rel}: brak statycznego DDL (op.*) — migracja musi być statyczna per tabela"
                )
            for symbol in _FORBIDDEN_DYNAMIC_SYMBOLS:
                if f"import {symbol}" in src or f"{symbol}(" in src:
                    violations.append(
                        f"{rel}: użycie legacy dynamicznego baseline'u ({symbol}) zamiast "
                        "statycznej migracji per tabela"
                    )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_migration_baselines_use_orm_metadata",
        "warunek zapisany w asercji musi być spełniony",
        "Migracje muszą być statyczne per tabela (op.create_table/op.drop_table/op.*), bez "
        "dynamicznych helperów ORM metadata (apply_baseline / create_service_tables / "
        "apply_delivery_baseline / create_all). Legacy wzorzec jest zabroniony — refaktor "
        "wykonywany do końca:\n" + "\n".join(violations),
    )
