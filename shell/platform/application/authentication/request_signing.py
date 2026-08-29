"""Request signing — HMAC-SHA256 request signing for cross-service HTTP auth.

Adds a short-lived, method- and path-bound signature to outgoing requests so a
receiver can authenticate a SYSTEM caller without a long-lived shared token in
every header. The shared secret remains the per-service API key; the signature
proves possession of it for exactly one request within a replay window.
"""

from __future__ import annotations

import hashlib
import hmac
import time

SIGNATURE_HEADER = "X-Shell-Signature"
TIMESTAMP_HEADER = "X-Shell-Timestamp"


def _payload(method: str, path: str, timestamp: int) -> str:
    return f"{method}\n{path}\n{timestamp}"


def sign_request(*, secret: str, method: str, path: str, timestamp: int | None = None) -> str:
    stamp = int(time.time()) if timestamp is None else timestamp
    payload = _payload(method.upper(), path, stamp)
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_signature(
    *,
    secret: str,
    method: str,
    path: str,
    timestamp: int | None,
    signature: str,
    now: int | None = None,
    max_age_seconds: int = 300,
) -> bool:
    if not signature or timestamp is None:
        return False
    current = int(time.time()) if now is None else now
    if abs(current - timestamp) > max_age_seconds:
        return False
    expected = sign_request(
        secret=secret,
        method=method,
        path=path,
        timestamp=timestamp,
    )
    return hmac.compare_digest(expected, signature)


__all__ = ["SIGNATURE_HEADER", "TIMESTAMP_HEADER", "sign_request", "verify_signature"]
