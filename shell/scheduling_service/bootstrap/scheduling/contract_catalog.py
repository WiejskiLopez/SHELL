"""Scheduling bounded context contract catalog — explicit public allowlist.

The catalog is NOT a derived view of the registry: every public contract is
declared explicitly here with its owner, producers and consumers. Adding an
event to the registry without an explicit catalog entry fails the architecture
test (``test_contract_catalog.py``).
"""

from __future__ import annotations

from shell.platform.application.contracts.contract_catalog import (
    ContractEntry,
    build_contract_catalog,
)

OWNER = "scheduling"

_CONTRACTS: tuple[ContractEntry, ...] = (
    ContractEntry(
        type_name="SchedulerDefinitionCreatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="SchedulerDefinitionDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="SchedulerDefinitionUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="SchedulerExecutionCompletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="SchedulerExecutionDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="SchedulerExecutionFailedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="SchedulerExecutionSkippedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="SchedulerExecutionStartedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="SchedulerExecutionUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="SchedulerJobCreatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="SchedulerJobDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="SchedulerJobUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
)


SCHEDULING_CONTRACT_CATALOG = build_contract_catalog(OWNER, _CONTRACTS)
