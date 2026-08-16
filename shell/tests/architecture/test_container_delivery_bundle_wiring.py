"""Koncept: reguła architektoniczna dotycząca container delivery bundle wiring.

Reguła: test sprawdza kontrakt architektoniczny container delivery bundle wiring.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from _arch_helpers import architecture_assertion_message

if TYPE_CHECKING:
    from collections.abc import Callable
_CONTAINERS: tuple[tuple[str, Callable[[], Callable[[], Any]]], ...] = (('definition', lambda: __import__('shell.definition_service.bootstrap.definition.container.definition_core_container', fromlist=['DefinitionCoreContainer']).DefinitionCoreContainer), ('execution', lambda: __import__('shell.execution_service.bootstrap.execution.container.execution_core_container', fromlist=['ExecutionCoreContainer']).ExecutionCoreContainer), ('ingestion', lambda: __import__('shell.ingestion_service.bootstrap.ingestion.container.ingestion_core_container', fromlist=['IngestionCoreContainer']).IngestionCoreContainer), ('project', lambda: __import__('shell.project_service.bootstrap.project.container.project_core_container', fromlist=['ProjectCoreContainer']).ProjectCoreContainer), ('scheduling', lambda: __import__('shell.scheduling_service.bootstrap.scheduling.container.scheduling_core_container', fromlist=['SchedulingCoreContainer']).SchedulingCoreContainer), ('session', lambda: __import__('shell.session_service.bootstrap.session.container.session_core_container', fromlist=['SessionCoreContainer']).SessionCoreContainer), ('user', lambda: __import__('shell.user_service.bootstrap.user.container.user_core_container', fromlist=['UserCoreContainer']).UserCoreContainer))

def test_each_bc_container_exposes_local_persistence_bundle() -> None:
    for bounded_context, container_factory in _CONTAINERS:
        container = container_factory()()
        assert container.persistence_delivery_models() is not None, architecture_assertion_message('reguła testowana przez test_each_bc_container_exposes_local_persistence_bundle', 'warunek zapisany w asercji musi być spełniony', bounded_context)
