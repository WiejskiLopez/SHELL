"""Definition bounded context contract catalog — explicit public allowlist.

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

OWNER = "definition"

_CONTRACTS: tuple[ContractEntry, ...] = (
    ContractEntry(
        type_name="GraphDefinitionCreatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="GraphDefinitionDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="GraphDefinitionEmbeddingCreatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="GraphDefinitionEmbeddingDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="GraphDefinitionEmbeddingUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="GraphDefinitionUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="NodeDefinitionCreatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="NodeDefinitionDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="NodeDefinitionUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="NodeLinkDefinitionCreatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="NodeLinkDefinitionDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="NodeLinkDefinitionUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="RunnerConfigCreatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="RunnerConfigDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="RunnerConfigUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
)


DEFINITION_CONTRACT_CATALOG = build_contract_catalog(OWNER, _CONTRACTS)
