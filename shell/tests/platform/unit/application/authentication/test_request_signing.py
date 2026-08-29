"""Unit tests — HMAC request signing utilities."""

from __future__ import annotations

from shell.platform.application.authentication.request_signing import (
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    sign_request,
    verify_signature,
)


class TestRequestSigning:
    def test_round_trip_verifies(self) -> None:
        signature = sign_request(secret="shared", method="GET", path="/api/v1/data", timestamp=1000)

        assert verify_signature(
            secret="shared",
            method="GET",
            path="/api/v1/data",
            timestamp=1000,
            signature=signature,
            now=1000,
        )

    def test_signature_is_method_and_path_bound(self) -> None:
        signature = sign_request(secret="shared", method="GET", path="/api/v1/data", timestamp=1000)

        assert not verify_signature(
            secret="shared",
            method="POST",
            path="/api/v1/data",
            timestamp=1000,
            signature=signature,
            now=1000,
        )
        assert not verify_signature(
            secret="shared",
            method="GET",
            path="/api/v1/other",
            timestamp=1000,
            signature=signature,
            now=1000,
        )

    def test_tampered_signature_is_rejected(self) -> None:
        signature = sign_request(secret="shared", method="GET", path="/api/v1/data", timestamp=1000)
        tampered = ("b" if not signature.startswith("b") else "a") + signature[1:]

        assert not verify_signature(
            secret="shared",
            method="GET",
            path="/api/v1/data",
            timestamp=1000,
            signature=tampered,
            now=1000,
        )

    def test_stale_timestamp_is_rejected(self) -> None:
        signature = sign_request(secret="shared", method="GET", path="/api/v1/data", timestamp=1000)

        assert not verify_signature(
            secret="shared",
            method="GET",
            path="/api/v1/data",
            timestamp=1000,
            signature=signature,
            now=2000,
            max_age_seconds=300,
        )

    def test_future_timestamp_beyond_skew_is_rejected(self) -> None:
        signature = sign_request(secret="shared", method="GET", path="/api/v1/data", timestamp=1000)

        assert not verify_signature(
            secret="shared",
            method="GET",
            path="/api/v1/data",
            timestamp=1000,
            signature=signature,
            now=300,
            max_age_seconds=300,
        )

    def test_missing_timestamp_or_signature_is_rejected(self) -> None:
        signature = sign_request(secret="shared", method="GET", path="/api/v1/data", timestamp=1000)

        assert not verify_signature(
            secret="shared",
            method="GET",
            path="/api/v1/data",
            timestamp=None,
            signature=signature,
            now=1000,
        )
        assert not verify_signature(
            secret="shared",
            method="GET",
            path="/api/v1/data",
            timestamp=1000,
            signature="",
            now=1000,
        )

    def test_header_names_exposed(self) -> None:
        assert SIGNATURE_HEADER == "X-Shell-Signature"
        assert TIMESTAMP_HEADER == "X-Shell-Timestamp"
