"""Unit tests — uvicorn server bootstrap with optional (future) TLS/mTLS config."""

from __future__ import annotations

import ssl
from typing import TYPE_CHECKING

import pytest

from shell.platform.framework.bootstrap.server import (
    TlsConfig,
    build_service_uvicorn_config,
    tls_config_from_env,
)

if TYPE_CHECKING:
    import uvicorn

SERVICE = "execution"
_PREFIX = "EXECUTION_SERVICE_TLS"


def _clear_tls_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for suffix in ("CERTFILE", "KEYFILE", "CA_CERTS", "REQUIRE_CLIENT_CERT"):
        monkeypatch.delenv(f"{_PREFIX}_{suffix}", raising=False)


def _server_config() -> uvicorn.Config:
    return build_service_uvicorn_config(
        object(),
        service=SERVICE,
        host="127.0.0.1",
        port=8007,
    )


class TestTlsConfigFromEnv:
    def test_unset_returns_none(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_tls_env(monkeypatch)

        assert tls_config_from_env(SERVICE) is None

    def test_certfile_and_keyfile_resolved(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_tls_env(monkeypatch)
        monkeypatch.setenv(f"{_PREFIX}_CERTFILE", "/certs/server.crt")
        monkeypatch.setenv(f"{_PREFIX}_KEYFILE", "/certs/server.key")

        tls = tls_config_from_env(SERVICE)

        assert isinstance(tls, TlsConfig)
        assert tls.certfile == "/certs/server.crt"
        assert tls.keyfile == "/certs/server.key"
        assert tls.ca_certs is None
        assert tls.require_client_cert is False

    def test_client_cert_requirement_parsed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_tls_env(monkeypatch)
        monkeypatch.setenv(f"{_PREFIX}_CERTFILE", "/certs/server.crt")
        monkeypatch.setenv(f"{_PREFIX}_KEYFILE", "/certs/server.key")
        monkeypatch.setenv(f"{_PREFIX}_CA_CERTS", "/certs/ca.pem")
        monkeypatch.setenv(f"{_PREFIX}_REQUIRE_CLIENT_CERT", "true")

        tls = tls_config_from_env(SERVICE)

        assert tls is not None
        assert tls.ca_certs == "/certs/ca.pem"
        assert tls.require_client_cert is True

    def test_certfile_without_keyfile_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_tls_env(monkeypatch)
        monkeypatch.setenv(f"{_PREFIX}_CERTFILE", "/certs/server.crt")

        with pytest.raises(ValueError):
            tls_config_from_env(SERVICE)

    def test_client_cert_without_ca_is_rejected(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_tls_env(monkeypatch)
        monkeypatch.setenv(f"{_PREFIX}_CERTFILE", "/certs/server.crt")
        monkeypatch.setenv(f"{_PREFIX}_KEYFILE", "/certs/server.key")
        monkeypatch.setenv(f"{_PREFIX}_REQUIRE_CLIENT_CERT", "true")

        with pytest.raises(ValueError):
            tls_config_from_env(SERVICE)


class TestBuildServiceUvicornConfig:
    def test_plain_http_without_tls(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_tls_env(monkeypatch)

        config = _server_config()

        assert config.ssl_certfile is None
        assert config.ssl_keyfile is None

    def test_tls_binds_certificate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_tls_env(monkeypatch)
        monkeypatch.setenv(f"{_PREFIX}_CERTFILE", "/certs/server.crt")
        monkeypatch.setenv(f"{_PREFIX}_KEYFILE", "/certs/server.key")

        config = _server_config()

        assert config.ssl_certfile == "/certs/server.crt"
        assert config.ssl_keyfile == "/certs/server.key"
        assert config.ssl_cert_reqs == ssl.CERT_NONE

    def test_mutual_tls_requires_client_certificate(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _clear_tls_env(monkeypatch)
        monkeypatch.setenv(f"{_PREFIX}_CERTFILE", "/certs/server.crt")
        monkeypatch.setenv(f"{_PREFIX}_KEYFILE", "/certs/server.key")
        monkeypatch.setenv(f"{_PREFIX}_CA_CERTS", "/certs/ca.pem")
        monkeypatch.setenv(f"{_PREFIX}_REQUIRE_CLIENT_CERT", "true")

        config = _server_config()

        assert config.ssl_ca_certs == "/certs/ca.pem"
        assert config.ssl_cert_reqs == ssl.CERT_REQUIRED

    def test_ca_without_requirement_verifies_optional_client(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        _clear_tls_env(monkeypatch)
        monkeypatch.setenv(f"{_PREFIX}_CERTFILE", "/certs/server.crt")
        monkeypatch.setenv(f"{_PREFIX}_KEYFILE", "/certs/server.key")
        monkeypatch.setenv(f"{_PREFIX}_CA_CERTS", "/certs/ca.pem")

        config = _server_config()

        assert config.ssl_ca_certs == "/certs/ca.pem"
        assert config.ssl_cert_reqs == ssl.CERT_OPTIONAL
