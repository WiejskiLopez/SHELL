from __future__ import annotations

import hashlib


def _compute_runner_config_hash(package_name: str, kind: str, body: str) -> str:
    h = hashlib.sha256()
    h.update(package_name.encode('utf-8'))
    h.update(b'\x00')
    h.update(kind.encode('utf-8'))
    h.update(b'\x00')
    h.update(body.encode('utf-8'))
    return h.hexdigest()
