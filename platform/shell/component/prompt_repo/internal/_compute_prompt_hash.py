from __future__ import annotations

import hashlib


def _compute_prompt_hash(kind: str, role: str | None, name: str, body: str) -> str:
    h = hashlib.sha256()
    h.update((kind or '').encode('utf-8'))
    h.update(b'\x00')
    h.update((role or '').encode('utf-8'))
    h.update(b'\x00')
    h.update((name or '').encode('utf-8'))
    h.update(b'\x00')
    h.update((body or '').encode('utf-8'))
    return h.hexdigest()
