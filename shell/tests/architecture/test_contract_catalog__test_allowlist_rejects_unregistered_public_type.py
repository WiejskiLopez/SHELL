"""Koncept: reguła architektoniczna dotycząca contract catalog: test allowlist rejects unregistered public type.

Reguła: test sprawdza kontrakt architektoniczny contract catalog: test allowlist rejects unregistered public type.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from _arch_helpers import architecture_assertion_message

if TYPE_CHECKING:
    from collections.abc import Callable
_CATALOG_MODULES: dict[str, str] = {'definition': 'shell.definition_service.bootstrap.definition.contract_catalog', 'execution': 'shell.execution_service.bootstrap.execution.contract_catalog', 'ingestion': 'shell.ingestion_service.bootstrap.ingestion.contract_catalog', 'project': 'shell.project_service.bootstrap.project.contract_catalog', 'scheduling': 'shell.scheduling_service.bootstrap.scheduling.contract_catalog', 'session': 'shell.session_service.bootstrap.session.contract_catalog', 'user': 'shell.user_service.bootstrap.user.contract_catalog'}
_REGISTRY_FACTORIES: dict[str, Callable[[], dict[str, type]]] = {'definition': lambda: __import__('shell.definition_service.bootstrap.definition.event_registry', fromlist=['build_definition_event_registry']).build_definition_event_registry(), 'execution': lambda: __import__('shell.execution_service.bootstrap.execution.event_registry', fromlist=['build_execution_event_registry']).build_execution_event_registry(), 'ingestion': lambda: __import__('shell.ingestion_service.bootstrap.ingestion.event_registry', fromlist=['build_ingestion_event_registry']).build_ingestion_event_registry(), 'project': lambda: __import__('shell.project_service.bootstrap.project.event_registry', fromlist=['build_project_event_registry']).build_project_event_registry(), 'scheduling': lambda: __import__('shell.scheduling_service.bootstrap.scheduling.event_registry', fromlist=['build_scheduling_event_registry']).build_scheduling_event_registry(), 'session': lambda: __import__('shell.session_service.bootstrap.session.event_registry', fromlist=['build_session_event_registry']).build_session_event_registry(), 'user': lambda: __import__('shell.user_service.bootstrap.user.event_registry', fromlist=['build_user_event_registry']).build_user_event_registry()}
_CATALOG_ATTR = {'definition': 'DEFINITION_CONTRACT_CATALOG', 'execution': 'EXECUTION_CONTRACT_CATALOG', 'ingestion': 'INGESTION_CONTRACT_CATALOG', 'project': 'PROJECT_CONTRACT_CATALOG', 'scheduling': 'SCHEDULING_CONTRACT_CATALOG', 'session': 'SESSION_CONTRACT_CATALOG', 'user': 'USER_CONTRACT_CATALOG'}
_INTEGRATION_EVENT_BASE_PATH = 'shell.platform.application.events.integration_event'

def _catalog_for(bounded_context: str) -> Any:
    module = __import__(_CATALOG_MODULES[bounded_context], fromlist=['_catalog'])
    return getattr(module, _CATALOG_ATTR[bounded_context])

def test_allowlist_rejects_unregistered_public_type() -> None:
    """A type without a catalog entry must not be exposed as a public contract.

    The catalog is an explicit allowlist (ref2.md §4.3, ref4.md Krok 5) — the
    enforcement mechanism rejects any registered type that has no entry, whether
    event, message or command.
    """
    from shell.platform.application.contracts.contract_catalog import (
        ContractEntry,
        build_contract_catalog,
    )
    catalog = build_contract_catalog('test-bc', (ContractEntry(type_name='AllowedEvent', owner='test-bc', supported_schema_versions=frozenset({1, 2})),))
    catalog.assert_covers(['AllowedEvent'])
    try:
        catalog.assert_covers(['AllowedEvent', 'SneakyCommand'])
    except ValueError as exc:
        assert 'SneakyCommand' in str(exc), architecture_assertion_message('reguła testowana przez test_allowlist_rejects_unregistered_public_type', 'warunek zapisany w asercji musi być spełniony', 'Asercja nie zawierała dodatkowych szczegółów.')
    else:
        raise AssertionError('assert_covers must reject an unregistered public type')
