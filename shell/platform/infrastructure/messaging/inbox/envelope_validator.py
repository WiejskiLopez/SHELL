"""EnvelopeValidator — validates inbox delivery records before deserialization.

Runs before deserialization so contract-level problems (unknown version, missing
ids, oversized payload) are classified explicitly instead of surfacing as generic
handler errors. An invalid envelope never raises: it returns a structured error
code that the processor maps to retry / DLQ policy.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from shell.platform.application.contracts.contract_catalog import ContractCatalog

DESERIALIZATION_ERROR = "DESERIALIZATION_ERROR"
UNSUPPORTED_SCHEMA_VERSION = "UNSUPPORTED_SCHEMA_VERSION"
INVALID_ENVELOPE = "INVALID_ENVELOPE"
PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
MISSING_DELIVERY_ID = "MISSING_DELIVERY_ID"
MISSING_CORRELATION_ID = "MISSING_CORRELATION_ID"
MISSING_CAUSATION_ID = "MISSING_CAUSATION_ID"


@dataclass(frozen=True, slots=True)
class EnvelopeValidationPolicy:
    """Supported schema versions per delivery type.

    A consumer supports the current and the previous version through an upcaster.
    The mapping keys are delivery type names; types not listed use
    ``default_supported_versions``.
    """

    supported_schema_versions: Mapping[str, frozenset[int]] = field(default_factory=dict)
    default_supported_versions: frozenset[int] = frozenset({1})
    max_payload_bytes: int = 1_000_000
    require_delivery_id: bool = True
    require_correlation_id: bool = False
    require_causation_id: bool = False


class EnvelopeValidator:
    def __init__(self, policy: EnvelopeValidationPolicy | None = None) -> None:
        self._policy = policy or EnvelopeValidationPolicy()

    def validate(
        self,
        *,
        delivery_id: str | None,
        message_name: str,
        schema_version: int,
        payload: object,
        correlation_id: str | None,
        causation_id: str | None,
    ) -> str | None:
        """Return an error code if the envelope is invalid, else ``None``."""
        if self._policy.require_delivery_id and not delivery_id:
            return MISSING_DELIVERY_ID
        if self._policy.require_correlation_id and not correlation_id:
            return MISSING_CORRELATION_ID
        if self._policy.require_causation_id and not causation_id:
            return MISSING_CAUSATION_ID

        supported = self._policy.supported_schema_versions.get(
            message_name, self._policy.default_supported_versions
        )
        if schema_version not in supported:
            return UNSUPPORTED_SCHEMA_VERSION

        if isinstance(payload, dict):
            size = _measure_payload(payload)
            if size > self._policy.max_payload_bytes:
                return PAYLOAD_TOO_LARGE

        return None


def _measure_payload(payload: dict[str, object]) -> int:
    total = 0
    for value in payload.values():
        if isinstance(value, str):
            total += len(value.encode("utf-8"))
        elif isinstance(value, (int, float, bool)):
            total += len(repr(value).encode("utf-8"))
        elif isinstance(value, dict):
            total += _measure_payload(value)
        elif isinstance(value, list):
            for item in value:
                total += len(str(item).encode("utf-8"))
    return total


def envelope_policy_from_catalog(
    catalog: ContractCatalog,
    *,
    default_supported_versions: frozenset[int] | None = None,
) -> EnvelopeValidationPolicy:
    """Build an :class:`EnvelopeValidationPolicy` from a BC contract catalog.

    ``supported_schema_versions`` of every catalog entry become the policy's
    per-type allowlist, so the catalog is the single source of truth for which
    schema versions a consumer accepts (ref4.md Krok 5).
    """
    supported: dict[str, frozenset[int]] = {
        entry.type_name: entry.supported_schema_versions for entry in catalog.entries
    }
    return EnvelopeValidationPolicy(
        supported_schema_versions=supported,
        default_supported_versions=default_supported_versions or frozenset({1}),
    )
