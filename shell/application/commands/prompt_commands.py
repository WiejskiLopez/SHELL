from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SavePromptCommand:
    name: str
    body: str
    source_uri: str = ""
