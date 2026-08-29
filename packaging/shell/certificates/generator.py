"""Generate a portable static CA and service certificate bundle."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from ipaddress import IPv4Address
from typing import TYPE_CHECKING

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID, NameOID

if TYPE_CHECKING:
    from pathlib import Path

DEFAULT_SERVICES = {
    "definition": "shell-definition-api",
    "session": "shell-session-api",
}


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
) -> x509.Certificate:
    builder = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(public_key)
        .serial_number(serial)
        .not_valid_before(not_before)
        .not_valid_after(not_before + timedelta(days=3650))
    )
    for extension, critical in extensions:
        builder = builder.add_extension(extension, critical)
    return builder.sign(issuer_key, hashes.SHA256())


def generate_bundle(
    output_dir: Path,
    *,
    services: dict[str, str] | None = None,
    client_name: str = "execution-client",
    force: bool = False,
) -> None:
    """Generate a CA, server certificates and one client certificate."""
    selected_services = services or DEFAULT_SERVICES
    output_dir.mkdir(parents=True, exist_ok=True)
    if not force and any(output_dir.glob("*.crt")):
        raise FileExistsError(f"Certificate files already exist in {output_dir}; use force=True")

    now = datetime.now(UTC)
    ca_key = _key()
    ca_name = _name("SHELL research mTLS CA")
    ca_cert = _certificate(
        ca_name,
        ca_name,
        ca_key.public_key(),
        ca_key,
        [(x509.BasicConstraints(ca=True, path_length=1), True)],
        1,
        now,
    )
    _write_key(output_dir / "ca.key", ca_key)
    (output_dir / "ca.crt").write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))

    for serial, (service, hostname) in enumerate(selected_services.items(), start=10):
        key = _key()
        cert = _certificate(
            _name(hostname),
            ca_name,
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
                (x509.ExtendedKeyUsage([ExtendedKeyUsageOID.SERVER_AUTH]), False),
            ],
            serial,
            now,
        )
        _write_key(output_dir / f"{service}.key", key)
        (output_dir / f"{service}.crt").write_bytes(
            cert.public_bytes(serialization.Encoding.PEM)
        )

    client_key = _key()
    client_cert = _certificate(
        _name(client_name),
        ca_name,
        client_key.public_key(),
        ca_key,
        [
            (x509.BasicConstraints(ca=False, path_length=None), True),
            (x509.ExtendedKeyUsage([ExtendedKeyUsageOID.CLIENT_AUTH]), False),
        ],
        20,
        now,
    )
    _write_key(output_dir / f"{client_name}.key", client_key)
    (output_dir / f"{client_name}.crt").write_bytes(
        client_cert.public_bytes(serialization.Encoding.PEM)
    )
