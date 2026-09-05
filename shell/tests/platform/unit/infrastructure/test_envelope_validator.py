"""Unit tests for the platform envelope validator."""

from __future__ import annotations

from shell.platform.infrastructure.messaging.inbox.envelope_validator import (
    MISSING_DELIVERY_ID,
    PAYLOAD_TOO_LARGE,
    UNSUPPORTED_SCHEMA_VERSION,
    EnvelopeValidationPolicy,
    EnvelopeValidator,
)


class TestEnvelopeValidator:
    def test_accepts_supported_version(self) -> None:
        validator = EnvelopeValidator(
            EnvelopeValidationPolicy(supported_schema_versions={"SampleEvent": frozenset({1, 2})})
        )
        error = validator.validate(
            delivery_id="delivery-1",
            message_name="SampleEvent",
            schema_version=2,
            payload={},
            correlation_id="c",
            causation_id="k",
        )
        assert error is None

    def test_rejects_unknown_newer_version(self) -> None:
        validator = EnvelopeValidator(
            EnvelopeValidationPolicy(supported_schema_versions={"SampleEvent": frozenset({1})})
        )
        error = validator.validate(
            delivery_id="delivery-1",
            message_name="SampleEvent",
            schema_version=99,
            payload={},
            correlation_id="c",
            causation_id="k",
        )
        assert error == UNSUPPORTED_SCHEMA_VERSION

    def test_default_supported_version_is_one(self) -> None:
        validator = EnvelopeValidator(EnvelopeValidationPolicy())
        assert (
            validator.validate(
                delivery_id="delivery-1",
                message_name="AnyEvent",
                schema_version=1,
                payload={},
                correlation_id="c",
                causation_id="k",
            )
            is None
        )
        assert (
            validator.validate(
                delivery_id="delivery-1",
                message_name="AnyEvent",
                schema_version=2,
                payload={},
                correlation_id="c",
                causation_id="k",
            )
            == UNSUPPORTED_SCHEMA_VERSION
        )

    def test_missing_delivery_id_rejected_when_required(self) -> None:
        validator = EnvelopeValidator(EnvelopeValidationPolicy(require_delivery_id=True))
        error = validator.validate(
            delivery_id=None,
            message_name="AnyEvent",
            schema_version=1,
            payload={},
            correlation_id="c",
            causation_id="k",
        )
        assert error == MISSING_DELIVERY_ID

    def test_oversized_payload_rejected(self) -> None:
        validator = EnvelopeValidator(EnvelopeValidationPolicy(max_payload_bytes=10))
        error = validator.validate(
            delivery_id="delivery-1",
            message_name="AnyEvent",
            schema_version=1,
            payload={"big": "x" * 100},
            correlation_id="c",
            causation_id="k",
        )
        assert error == PAYLOAD_TOO_LARGE
