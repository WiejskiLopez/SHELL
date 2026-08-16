"""Koncept: reguła architektoniczna dotycząca standalone service surfaces: test service surface does not depend on legacy monolith.

Reguła: test sprawdza kontrakt architektoniczny standalone service surfaces: test service surface does not depend on legacy monolith.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

from _arch_helpers import BASE, architecture_assertion_message

_BCS = ('definition_service', 'execution_service', 'ingestion_service', 'project_service', 'scheduling_service', 'session_service', 'user_service')

def test_service_surface_does_not_depend_on_legacy_monolith() -> None:
    legacy_root = BASE / 'bootstrap' / 'monolith'
    assert not legacy_root.exists(), architecture_assertion_message('reguła testowana przez test_service_surface_does_not_depend_on_legacy_monolith', 'warunek zapisany w asercji musi być spełniony', f'Legacy monolith still exists: {legacy_root}')
