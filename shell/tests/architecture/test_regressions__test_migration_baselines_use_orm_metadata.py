"""Koncept: reguła architektoniczna dotycząca regressions: test baselines use ORM metadata.

Reguła: test sprawdza kontrakt architektoniczny regressions: test baselines use ORM metadata.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import BASE, architecture_assertion_message, iter_py_files


def test_migration_baselines_use_orm_metadata() -> None:
    violations: list[str] = []
    for service_root in (BASE / "platform", *sorted(BASE.glob("*_service"))):
        migrations_dir = service_root / "migrations" / "versions"
        if not migrations_dir.is_dir():
            continue
        for path in iter_py_files(migrations_dir):
            rel = path.relative_to(BASE).as_posix()
            src = path.read_text(encoding="utf-8")
            if "create_service_tables" not in src and "op.create_table" in src:
                violations.append(
                    f"{rel}: ręczne op.create_table zamiast create_service_tables z ORM metadata"
                )
    assert not violations, architecture_assertion_message(
        "reguła testowana przez test_migration_baselines_use_orm_metadata",
        "warunek zapisany w asercji musi być spełniony",
        "Migracje baseline muszą pochodzić z ORM metadata (create_service_tables), aby typy "
        "(JSONB/timestamptz/version) nie rozjechały się z modelami:\n" + "\n".join(violations),
    )
