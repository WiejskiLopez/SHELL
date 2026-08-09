from __future__ import annotations

import secrets


class SecureTokenGenerator:
    def generate(self) -> str:
        return secrets.token_urlsafe(32)
