from __future__ import annotations

from dataclasses import dataclass, field

from shell_ddd.domain.value_objects.ids import TemplateGraphNodeId
from shell_ddd.domain.value_objects.mode import Mode


@dataclass(slots=True)
class TemplateGraphNode:
    id: TemplateGraphNodeId
    position: int
    mode: Mode
    role: str
    node_type: str
    model: str = ""
    command: str = ""
    timeout: int = 0
    retries: int = 0
    log_level: str = "INFO"
    max_step: int | None = None
    no_ask_user: bool = False
    autopilot: bool = False
    status_initial: str = ""
    extra: dict[str, object] = field(default_factory=dict)
    script: str = ""
    script_type: str = ""