from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ArchiveEnvelopeCommand:
    envelope_id: str

    @classmethod
    def validate(cls) -> None:
        pass
