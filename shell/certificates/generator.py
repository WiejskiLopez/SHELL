"""Generate a portable static CA and service certificate bundle."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from ipaddress import IPv4Address
from typing import TYPE_CHECKING

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import random_serial_number
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

if TYPE_CHECKING:
    from pathlib import Path

CA_CERTIFICATE = "ca.crt"
CA_PRIVATE_KEY = "ca.key"
DEFAULT_CA_LIFETIME_DAYS = 1825
DEFAULT_CERTIFICATE_LIFETIME_DAYS = 365


def _key() -> rsa.RSAPrivateKey:
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


def _name(common_name: str) -> x509.Name:
    return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])


def _write_key(path: Path, key: rsa.RSAPrivateKey) -> None:
    path.write_bytes(
        key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )


def _certificate(
    subject: x509.Name,
    issuer: x509.Name,
    public_key: rsa.RSAPublicKey,
    issuer_key: rsa.RSAPrivateKey,
    extensions: list[tuple[x509.ExtensionType, bool]],
    serial: int,
    not_before: datetime,
    lifetime_days: int,
) -> x509.Certificate:
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(serial)
        .not_valid_before(not_before)
        .not_valid_after(not_before + timedelta(days=lifetime_days))
    )
    for extension, critical in extensions:
        builder = builder.add_extension(extension, critical)
    return builder.sign(issuer_key, hashes.SHA256())


def _load_ca(ca_dir: Path) -> tuple[rsa.RSAPrivateKey, x509.Certificate]:
    key = serialization.load_pem_private_key((ca_dir / CA_PRIVATE_KEY).read_bytes(), password=None)
    certificate = x509.load_pem_x509_certificate((ca_dir / CA_CERTIFICATE).read_bytes())
    if not isinstance(key, rsa.RSAPrivateKey):
        raise TypeError("CA private key must be RSA")
    return key, certificate


def ensure_ca(
    ca_dir: Path,
    *,
    lifetime_days: int = DEFAULT_CA_LIFETIME_DAYS,
    now: datetime | None = None,
    force: bool = False,
) -> bool:
    """Ensure a valid persistent CA exists; return True when a new CA was created."""
    ca_dir.mkdir(parents=True, exist_ok=True)
    current_time = now or datetime.now(UTC)
    certificate_path = ca_dir / CA_CERTIFICATE
    key_path = ca_dir / CA_PRIVATE_KEY
    if not force and certificate_path.exists() and key_path.exists():
        try:
            _, certificate = _load_ca(ca_dir)
            if certificate.not_valid_before_utc <= current_time < certificate.not_valid_after_utc:
                return False
        except (ValueError, TypeError):
            pass

    ca_key = _key()
    ca_name = _name("SHELL research mTLS CA")
    ca_cert = _certificate(
        ca_name,
        ca_name,
        ca_key.public_key(),
        ca_key,
        [
            (x509.BasicConstraints(ca=True, path_length=1), True),
            (x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), False),
            (
                x509.KeyUsage(
                    digital_signature=True,
                    content_commitment=False,
                    key_encipherment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=True,
                    crl_sign=True,
                    encipher_only=False,
                    decipher_only=False,
                ),
                True,
            ),
        ],
        1,
        current_time,
        lifetime_days,
    )
    _write_key(key_path, ca_key)
    certificate_path.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))
    return True


def issue_certificate(
    ca_dir: Path,
    output_dir: Path,
    *,
    name: str,
    hostname: str,
    lifetime_days: int = DEFAULT_CERTIFICATE_LIFETIME_DAYS,
    now: datetime | None = None,
) -> None:
    """Issue a fresh service certificate signed by the persistent CA."""
    ca_key, ca_cert = _load_ca(ca_dir)
    current_time = now or datetime.now(UTC)
    if not (ca_cert.not_valid_before_utc <= current_time < ca_cert.not_valid_after_utc):
        raise ValueError("CA certificate is missing or expired; run ensure_ca first")
    key = _key()
    certificate = _certificate(
        _name(hostname),
        ca_cert.subject,
        key.public_key(),
        ca_key,
        [
            (x509.BasicConstraints(ca=False, path_length=None), True),
            (
                x509.SubjectAlternativeName(
                    [
                        x509.DNSName(hostname),
                        x509.DNSName("localhost"),
                        x509.IPAddress(IPv4Address("127.0.0.1")),
                    ]
                ),
                False,
            ),
            (
                x509.ExtendedKeyUsage(
                    [ExtendedKeyUsageOID.SERVER_AUTH, ExtendedKeyUsageOID.CLIENT_AUTH]
                ),
                False,
            ),
            (x509.SubjectKeyIdentifier.from_public_key(key.public_key()), False),
            (
                x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
                False,
            ),
        ],
        random_serial_number(),
        current_time,
        lifetime_days,
    )
    output_dir.mkdir(parents=True, exist_ok=True)
    _write_key(output_dir / f"{name}.key", key)
    (output_dir / f"{name}.crt").write_bytes(certificate.public_bytes(serialization.Encoding.PEM))
    (output_dir / CA_CERTIFICATE).write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))


def generate_bundle(output_dir: Path, *, force: bool = False) -> None:
    """Compatibility helper: ensure a CA and issue the default research certificates."""
    ensure_ca(output_dir, force=force)
    for name, hostname in {
        "definition": "shell-definition-api",
        "session": "shell-session-api",
        "execution": "shell-execution-api",
    }.items():
        issue_certificate(output_dir, output_dir, name=name, hostname=hostname)
