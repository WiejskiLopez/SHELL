"""Real TLS/mTLS round-trip tests built on the platform certificate generator.

Spins a loopback TLS server that requires a client certificate and asserts:
- a client presenting a certificate signed by the CA can exchange data;
- a client without a certificate cannot obtain an application response;
- ``ResilientAsyncClient`` with a per-service identity works against a real TLS
  server (``verify`` + ``cert`` wiring end-to-end).
"""

from __future__ import annotations

import socket
import ssl
import threading
from contextlib import contextmanager
from typing import TYPE_CHECKING

import pytest

from shell.certificates.generator import ensure_ca, issue_certificate

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

HTTP_OK = b"HTTP/1.1 200 OK\r\ncontent-length: 2\r\n\r\nOK"


def _bundle(tmp_path: Path) -> tuple[str, str, str, str, str]:
    ca_dir = tmp_path / "ca"
    ensure_ca(ca_dir)
    issue_certificate(ca_dir, tmp_path, name="server", hostname="shell-definition-api")
    issue_certificate(ca_dir, tmp_path, name="client", hostname="shell-execution-api")
    return (
        str(tmp_path / "ca.crt"),
        str(tmp_path / "server.crt"),
        str(tmp_path / "server.key"),
        str(tmp_path / "client.crt"),
        str(tmp_path / "client.key"),
    )


@contextmanager
def _tls_server(
    ca: str,
    certfile: str,
    keyfile: str,
) -> Iterator[int]:
    """Loopback TLS server that only completes application data with a trusted client cert."""
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(certfile, keyfile)
    context.load_verify_locations(ca)
    context.verify_mode = ssl.CERT_REQUIRED

    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = int(listener.getsockname()[1])

    def _serve() -> None:
        try:
            connection, _ = listener.accept()
        except OSError:
            return
        with connection:
            connection.settimeout(10)
            try:
                with context.wrap_socket(connection, server_side=True) as tls:
                    data = tls.recv(64)
                    if data:
                        tls.sendall(HTTP_OK)
            except Exception:
                return

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()
    try:
        yield port
    finally:
        listener.close()
        thread.join(timeout=5)


def _exchange(
    ca: str,
    port: int,
    certfile: str | None = None,
    keyfile: str | None = None,
) -> bytes:
    context = ssl.create_default_context(cafile=ca)
    if certfile is not None:
        context.load_cert_chain(certfile, keyfile)
    with (
        socket.create_connection(("127.0.0.1", port), timeout=10) as sock,
        context.wrap_socket(sock, server_hostname="127.0.0.1") as tls,
    ):
        tls.sendall(b"GET /health HTTP/1.1\r\nHost: shell-definition-api\r\n\r\n")
        return tls.recv(64)


class TestMtlsRoundTrip:
    def test_client_with_trusted_certificate_gets_http_200(self, tmp_path: Path) -> None:
        ca, server_crt, server_key, client_crt, client_key = _bundle(tmp_path)
        with _tls_server(ca, server_crt, server_key) as port:
            data = _exchange(ca, port, client_crt, client_key)

        assert data.startswith(b"HTTP/1.1 200 OK")

    def test_client_without_certificate_cannot_exchange_data(self, tmp_path: Path) -> None:
        ca, server_crt, server_key, _, _ = _bundle(tmp_path)
        with _tls_server(ca, server_crt, server_key) as port:
            try:
                data = _exchange(ca, port)
            except Exception:  # noqa: BLE001 — rejected client may raise on write/read
                data = b""

        assert data != HTTP_OK

    @pytest.mark.asyncio
    async def test_resilient_client_uses_per_service_identity_over_mtls(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        ca, server_crt, server_key, client_crt, client_key = _bundle(tmp_path)
        monkeypatch.setenv("EXECUTION_SERVICE_MTLS_CA_CERTS", ca)
        monkeypatch.setenv("EXECUTION_SERVICE_MTLS_CERTFILE", client_crt)
        monkeypatch.setenv("EXECUTION_SERVICE_MTLS_KEYFILE", client_key)

        from shell.platform.infrastructure.context.client import ResilientAsyncClient

        with _tls_server(ca, server_crt, server_key) as port:
            async with ResilientAsyncClient(
                tls_identity="execution",
                base_url=f"https://127.0.0.1:{port}",
            ) as client:
                response = await client.get("/health")

        assert response.status_code == 200
