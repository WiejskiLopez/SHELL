from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class BootstrapRunnerConfigCommand:
    package_name: str
    kind: str
    body: dict[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.package_name:
            raise ValueError("package_name cannot be empty")
        if not self.kind:
            raise ValueError("kind cannot be empty")
