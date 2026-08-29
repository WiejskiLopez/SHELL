from __future__ import annotations

import ssl
from datetime import UTC, datetime, timedelta
from ipaddress import IPv4Address

import httpx
import pytest
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import ExtendedKeyUsageOID

from shell.platform.application.authentication.request_signing import (
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    verify_signature,
)
from shell.platform.infrastructure.context.client import (
    CorrelationIdAsyncClient,
    ResilientAsyncClient,
    client_tls_kwargs_from_env,
)
from shell.platform.infrastructure.context.resilience import (
    CircuitBreakerPolicy,
    CircuitOpenError,
    RetryPolicy,
)


def _write_tls_bundle(path) -> tuple[str, str, str]:
    ca_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    ca_name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, "SHELL test CA")])
    ca_cert = (
        x509.CertificateBuilder()
        .subject_name(ca_name)
        .issuer_name(ca_name)
        .public_key(ca_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False
        )
        .sign(ca_key, hashes.SHA256())
    )
    ca_path = path / "ca.crt"
    ca_path.write_bytes(ca_cert.public_bytes(serialization.Encoding.PEM))

    client_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    client_name = x509.Name([x509.NameAttribute(x509.NameOID.COMMON_NAME, "test client")])
    client_cert = (
        x509.CertificateBuilder()
        .subject_name(client_name)
        .issuer_name(ca_cert.subject)
        .public_key(client_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(UTC) - timedelta(days=1))
        .not_valid_after(datetime.now(UTC) + timedelta(days=30))
        .add_extension(x509.BasicConstraints(ca=False, path_length=None), critical=True)
        .add_extension(
            x509.SubjectKeyIdentifier.from_public_key(client_key.public_key()), critical=False
        )
        .add_extension(
            x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()),
            critical=False,
        )
        .add_extension(
            x509.SubjectAlternativeName(
                [x509.DNSName("localhost"), x509.IPAddress(IPv4Address("127.0.0.1"))]
            ),
            critical=False,
        )
        .add_extension(
            x509.ExtendedKeyUsage(
                [ExtendedKeyUsageOID.SERVER_AUTH, ExtendedKeyUsageOID.CLIENT_AUTH]
            ),
            critical=False,
        )
        .sign(ca_key, hashes.SHA256())
    )
    client_crt = path / "client.crt"
    client_key_path = path / "client.key"
    client_crt.write_bytes(client_cert.public_bytes(serialization.Encoding.PEM))
    client_key_path.write_bytes(
        client_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.TraditionalOpenSSL,
            serialization.NoEncryption(),
        )
    )
    return str(ca_path), str(client_crt), str(client_key_path)


def test_client_tls_configuration_is_disabled_without_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for name in ("SHELL_MTLS_CA_CERTS", "SHELL_MTLS_CERTFILE", "SHELL_MTLS_KEYFILE"):
        monkeypatch.delenv(name, raising=False)

    assert client_tls_kwargs_from_env() == {}


def test_client_tls_configuration_requires_complete_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SHELL_MTLS_CA_CERTS", "/certs/ca.crt")
    monkeypatch.delenv("SHELL_MTLS_CERTFILE", raising=False)
    monkeypatch.delenv("SHELL_MTLS_KEYFILE", raising=False)

    with pytest.raises(ValueError, match="requires _CA_CERTS"):
        client_tls_kwargs_from_env()


def test_client_tls_uses_per_service_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    ca, client_crt, client_key = _write_tls_bundle(tmp_path)
    monkeypatch.delenv("SHELL_MTLS_CA_CERTS", raising=False)
    monkeypatch.setenv("EXECUTION_SERVICE_MTLS_CA_CERTS", ca)
    monkeypatch.setenv("EXECUTION_SERVICE_MTLS_CERTFILE", client_crt)
    monkeypatch.setenv("EXECUTION_SERVICE_MTLS_KEYFILE", client_key)

    kwargs = client_tls_kwargs_from_env("execution")

    assert set(kwargs) == {"verify"}
    assert kwargs["verify"].verify_mode != ssl.CERT_NONE


def test_client_tls_per_service_requires_complete_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EXECUTION_SERVICE_MTLS_CA_CERTS", "/certs/ca.crt")
    monkeypatch.delenv("EXECUTION_SERVICE_MTLS_CERTFILE", raising=False)
    monkeypatch.delenv("EXECUTION_SERVICE_MTLS_KEYFILE", raising=False)

    with pytest.raises(ValueError, match="EXECUTION_SERVICE_MTLS requires"):
        client_tls_kwargs_from_env("execution")


@pytest.mark.asyncio
async def test_resilient_client_uses_per_service_tls_identity(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
) -> None:
    ca, client_crt, client_key = _write_tls_bundle(tmp_path)
    monkeypatch.setenv("EXECUTION_SERVICE_MTLS_CA_CERTS", ca)
    monkeypatch.setenv("EXECUTION_SERVICE_MTLS_CERTFILE", client_crt)
    monkeypatch.setenv("EXECUTION_SERVICE_MTLS_KEYFILE", client_key)

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(204)

    async with ResilientAsyncClient(
        service_api_key="service-secret",
        transport=httpx.MockTransport(handler),
        base_url="http://test",
        tls_identity="execution",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_client_adds_service_api_key_to_outgoing_request() -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(dict(request.headers))
        return httpx.Response(204)

    async with CorrelationIdAsyncClient(
        service_api_key="service-secret",
        transport=httpx.MockTransport(handler),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 204
    assert seen_headers["x-api-key"] == "service-secret"


@pytest.mark.asyncio
async def test_client_signs_outgoing_request_with_hmac() -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(dict(request.headers))
        return httpx.Response(204)

    async with CorrelationIdAsyncClient(
        service_api_key="service-secret",
        transport=httpx.MockTransport(handler),
        base_url="http://test",
    ) as client:
        response = await client.get("/health")

    assert response.status_code == 204
    signature_key = SIGNATURE_HEADER.lower()
    timestamp_key = TIMESTAMP_HEADER.lower()
    signature = seen_headers[signature_key]
    timestamp = int(seen_headers[timestamp_key])
    assert verify_signature(
        secret="service-secret",
        method="GET",
        path="/health",
        timestamp=timestamp,
        signature=signature,
        now=timestamp,
        max_age_seconds=0,
    )


@pytest.mark.asyncio
async def test_client_does_not_override_explicit_service_api_key() -> None:
    seen_headers: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen_headers.update(dict(request.headers))
        return httpx.Response(204)

    async with CorrelationIdAsyncClient(
        service_api_key="default-secret",
        transport=httpx.MockTransport(handler),
        base_url="http://test",
    ) as client:
        await client.get("/health", headers={"X-API-Key": "request-secret"})

    assert seen_headers["x-api-key"] == "request-secret"


@pytest.mark.asyncio
async def test_resilient_client_retries_get_after_transient_failure() -> None:
    statuses = iter((503, 204))
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(next(statuses))

    async def sleeper(delay: float) -> None:
        delays.append(delay)

    async with ResilientAsyncClient(
        retry_policy=RetryPolicy(max_attempts=2, initial_delay=0.25, max_delay=1),
        transport=httpx.MockTransport(handler),
        sleeper=sleeper,
        base_url="http://test",
    ) as client:
        response = await client.get("/resource")

    assert response.status_code == 204
    assert attempts == 2
    assert delays == [0.25]


@pytest.mark.asyncio
async def test_resilient_client_retries_get_after_transport_timeout() -> None:
    attempts = 0
    delays: list[float] = []

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            raise httpx.ReadTimeout("dependency timed out", request=request)
        return httpx.Response(204, request=request)

    async def sleeper(delay: float) -> None:
        delays.append(delay)

    async with ResilientAsyncClient(
        retry_policy=RetryPolicy(max_attempts=2, initial_delay=0.25, max_delay=1),
        transport=httpx.MockTransport(handler),
        sleeper=sleeper,
        base_url="http://test",
    ) as client:
        response = await client.get("/resource")

    assert response.status_code == 204
    assert attempts == 2
    assert delays == [0.25]
    assert client.circuit_state == "closed"


@pytest.mark.asyncio
async def test_resilient_client_does_not_retry_post() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    async with ResilientAsyncClient(
        retry_policy=RetryPolicy(max_attempts=3),
        transport=httpx.MockTransport(handler),
        base_url="http://test",
    ) as client:
        response = await client.post("/resource")

    assert response.status_code == 503
    assert attempts == 1


@pytest.mark.asyncio
async def test_resilient_client_opens_circuit_after_failures() -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(503)

    async with ResilientAsyncClient(
        retry_policy=RetryPolicy(max_attempts=1),
        circuit_breaker_policy=CircuitBreakerPolicy(failure_threshold=1),
        transport=httpx.MockTransport(handler),
        base_url="http://test",
    ) as client:
        response = await client.get("/resource")
        with pytest.raises(CircuitOpenError):
            await client.get("/resource")

    assert response.status_code == 503
    assert attempts == 1
