from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.x509.oid import ExtendedKeyUsageOID

from shell.certificates.generator import ensure_ca, issue_certificate

if TYPE_CHECKING:
    from pathlib import Path


def _certificate(path: Path) -> x509.Certificate:
    return x509.load_pem_x509_certificate(path.read_bytes())


def test_ensure_ca_reuses_valid_ca_and_recreates_expired_ca(tmp_path: Path) -> None:
    created_at = datetime(2026, 1, 1, tzinfo=UTC)

    assert ensure_ca(tmp_path, lifetime_days=1825, now=created_at) is True
    original = (tmp_path / "ca.crt").read_bytes()
    assert ensure_ca(tmp_path, lifetime_days=1825, now=created_at + timedelta(days=1)) is False
    assert (tmp_path / "ca.crt").read_bytes() == original

    assert ensure_ca(tmp_path, lifetime_days=1825, now=created_at + timedelta(days=1826)) is True
    assert (tmp_path / "ca.crt").read_bytes() != original


def _public_bytes(certificate: x509.Certificate) -> bytes:
    return certificate.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )


def test_issue_certificate_creates_unique_identity_signed_by_ca(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    ensure_ca(tmp_path, lifetime_days=1825, now=now)
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    issue_certificate(tmp_path, first_dir, name="first", hostname="first", now=now)
    issue_certificate(tmp_path, second_dir, name="second", hostname="second", now=now)

    ca = _certificate(tmp_path / "ca.crt")
    first = _certificate(first_dir / "first.crt")
    second = _certificate(second_dir / "second.crt")
    assert first.issuer == ca.subject == second.issuer
    assert _public_bytes(first) != _public_bytes(second)
    assert first.subject != second.subject


def test_ca_and_leaf_extensions_enable_mtls(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    ensure_ca(tmp_path, now=now)
    output = tmp_path / "leaf"
    issue_certificate(tmp_path, output, name="svc", hostname="shell-svc-api", now=now)

    ca = _certificate(tmp_path / "ca.crt")
    leaf = _certificate(output / "svc.crt")

    ca_basic = ca.extensions.get_extension_for_class(x509.BasicConstraints)
    assert ca_basic.value.ca is True
    ca_usage = ca.extensions.get_extension_for_class(x509.KeyUsage)
    assert ca_usage.value.key_cert_sign is True

    leaf_aki = leaf.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier).value
    ca_ski = ca.extensions.get_extension_for_class(x509.SubjectKeyIdentifier).value
    assert leaf_aki.key_identifier == ca_ski.digest

    leaf_basic = leaf.extensions.get_extension_for_class(x509.BasicConstraints)
    assert leaf_basic.value.ca is False

    leaf_eku = leaf.extensions.get_extension_for_class(x509.ExtendedKeyUsage).value
    assert any(oid == ExtendedKeyUsageOID.SERVER_AUTH for oid in leaf_eku)
    assert any(oid == ExtendedKeyUsageOID.CLIENT_AUTH for oid in leaf_eku)

    leaf_san = leaf.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
    assert "shell-svc-api" in leaf_san.get_values_for_type(x509.DNSName)
    assert "localhost" in leaf_san.get_values_for_type(x509.DNSName)

    validity = leaf.not_valid_after_utc - leaf.not_valid_before_utc
    assert timedelta(days=364) < validity <= timedelta(days=366)


def test_issue_certificate_honors_lifetime_days(tmp_path: Path) -> None:
    now = datetime(2026, 1, 1, tzinfo=UTC)
    ensure_ca(tmp_path, now=now)
    output = tmp_path / "short"
    issue_certificate(tmp_path, output, name="svc", hostname="h", lifetime_days=30, now=now)

    leaf = _certificate(output / "svc.crt")
    validity = leaf.not_valid_after_utc - leaf.not_valid_before_utc
    assert validity == timedelta(days=30)
