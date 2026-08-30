"""Koncept: reguła architektoniczna dotycząca enterprise patterns: test composition root in bootstrap.

Reguła: test sprawdza kontrakt architektoniczny enterprise patterns: test composition root in bootstrap.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    SERVICE_ROOTS,
    architecture_assertion_message,
    iter_py_files,
)


def test_composition_root_in_bootstrap() -> None:
    missing: list[str] = []
    for service_root in SERVICE_ROOTS:
        bootstrap_dir = service_root / "bootstrap"
        if not bootstrap_dir.exists():
            missing.append(f"{service_root.relative_to(BASE)}: missing bootstrap/ directory")
            continue
        container_files = list(bootstrap_dir.rglob("*container*.py"))
        factory_files = list(bootstrap_dir.rglob("*factory*.py"))
        if not container_files and not factory_files:
            found_composition = False
            for path in iter_py_files(bootstrap_dir):
                content = path.read_text(encoding="utf-8")
                if "Container" in content or "Factory" in content:
                    found_composition = True
                    break
            if not found_composition:
                missing.append(
                    f"{service_root.relative_to(BASE)}: bootstrap/ has no Container/Factory"
                )
    assert not missing, architecture_assertion_message(
        "reguła testowana przez test_composition_root_in_bootstrap",
        "warunek zapisany w asercji musi być spełniony",
        "bootstrap/ should contain Container or Factory files for DI composition:\n"
        + "\n".join(missing),
    )
