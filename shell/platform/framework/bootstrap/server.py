"""Server bootstrap — builds the uvicorn config for a service entrypoint.

Mutual TLS (mTLS) is prepared here as a **future configuration**: when a
service sets its TLS environment variables, the server binds TLS and —
optionally — requires a client certificate verified against a CA. By default
no TLS is configured (plain HTTP behind an edge/mesh proxy). Without a real CA
and issued certificates this path stays disabled.
"""

from __future__ import annotations

import os
import ssl
from dataclasses import dataclass
from typing import Any

import uvicorn


@dataclass(frozen=True, slots=True)
class TlsConfig:
    """Server-side TLS/mTLS settings resolved from environment variables."""

    certfile: str
    keyfile: str
    ca_certs: str | None = None
    require_client_cert: bool = False

    def __post_init__(self) -> None:
        if not self.certfile or not self.keyfile:
            raise ValueError("TLS requires certfile and keyfile")
        if self.require_client_cert and not self.ca_certs:
            raise ValueError("mutual TLS requires ca_certs when client certs are required")


def _env_value(name: str) -> str:
    return os.environ.get(name, "")


def tls_config_from_env(service: str) -> TlsConfig | None:
    """Build :class:`TlsConfig` from ``{SERVICE}_SERVICE_TLS_*``; None when unset."""
    prefix = f"{service.upper()}_SERVICE_TLS"
    certfile = _env_value(f"{prefix}_CERTFILE")
    keyfile = _env_value(f"{prefix}_KEYFILE")
    if not certfile and not keyfile:
        return None
    ca_certs = _env_value(f"{prefix}_CA_CERTS") or None
    require = _env_value(f"{prefix}_REQUIRE_CLIENT_CERT").lower() in ("1", "true", "yes")
    return TlsConfig(
        certfile=certfile,
        keyfile=keyfile,
        ca_certs=ca_certs,
        require_client_cert=require,
    )


def build_service_uvicorn_config(
    app: Any,
    *,
    service: str,
    host: str,
    port: int,
    reload: bool = False,
) -> uvicorn.Config:
    """Build a uvicorn config, enabling TLS/mTLS when the service configures it."""
    tls = tls_config_from_env(service)
    if tls is None:
        return uvicorn.Config(app, host=host, port=port, reload=reload)
    ssl_cert_reqs = ssl.CERT_NONE
    if tls.require_client_cert:
        ssl_cert_reqs = ssl.CERT_REQUIRED
    elif tls.ca_certs is not None:
        ssl_cert_reqs = ssl.CERT_OPTIONAL
    return uvicorn.Config(
        app,
        host=host,
        port=port,
        reload=reload,
        ssl_certfile=tls.certfile,
        ssl_keyfile=tls.keyfile,
        ssl_ca_certs=tls.ca_certs,
        ssl_cert_reqs=ssl_cert_reqs,
    )
