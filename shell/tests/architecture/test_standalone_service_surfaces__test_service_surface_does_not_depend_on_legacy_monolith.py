"""Koncept: reguła architektoniczna dotycząca standalone service surfaces: test service surface does not depend on legacy monolith.

Reguła: test sprawdza kontrakt architektoniczny standalone service surfaces: test service surface does not depend on legacy monolith.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from _arch_helpers import (
    BASE,
    architecture_assertion_message,
    iter_layer_dirs,
)


def test_service_surface_does_not_depend_on_legacy_monolith() -> None:
    found: list[str] = []
    for bootstrap_dir in iter_layer_dirs("bootstrap"):
        for legacy in bootstrap_dir.rglob("monolith"):
            if legacy.is_dir():
                found.append(legacy.relative_to(BASE).as_posix())
    assert not found, architecture_assertion_message(
        "reguła testowana przez test_service_surface_does_not_depend_on_legacy_monolith",
        "warunek zapisany w asercji musi być spełniony",
        "Legacy monolith still exists in a bootstrap/:\n" + "\n".join(found),
    )
