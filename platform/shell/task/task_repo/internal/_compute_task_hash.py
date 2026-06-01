from __future__ import annotations

import hashlib


def _compute_task_hash(body_md: str, body_yaml_raw: str) -> str:
    h = hashlib.sha256()
    h.update(body_md.encode("utf-8"))
    h.update(b"\x00")
    h.update(body_yaml_raw.encode("utf-8"))
    return h.hexdigest()
