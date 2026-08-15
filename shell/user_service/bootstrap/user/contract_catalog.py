"""User bounded context contract catalog — explicit public allowlist.

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

OWNER = "user"

_CONTRACTS: tuple[ContractEntry, ...] = (
    ContractEntry(
        type_name="AuthSessionCreatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="AuthSessionDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="AuthSessionRevokedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="AuthSessionUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="UserCreatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="UserDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="UserSkillCreatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="UserSkillDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="UserSkillUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="UserStateChangedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="UserStateDeletedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="UserStateUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
    ContractEntry(
        type_name="UserUpdatedIntegrationEvent",
        owner=OWNER,
        supported_schema_versions=frozenset({1}),
        producers=(OWNER,),
    ),
)


USER_CONTRACT_CATALOG = build_contract_catalog(OWNER, _CONTRACTS)
