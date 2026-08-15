"""Ingestion bounded context contract catalog — explicit public allowlist.

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

OWNER = "ingestion"

_CONTRACTS: tuple[ContractEntry, ...] = (
    ContractEntry(
        type_name="IngestionCreatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="IngestionDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="IngestionUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
)


INGESTION_CONTRACT_CATALOG = build_contract_catalog(OWNER, _CONTRACTS)
