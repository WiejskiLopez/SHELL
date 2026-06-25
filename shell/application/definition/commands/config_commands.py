from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class BootstrapRunnerConfigCommand:
    package_name: str
    kind: str
    body: dict[str, object] = field(default_factory=dict)

    @classmethod
    def validate(cls) -> None:
        pass
