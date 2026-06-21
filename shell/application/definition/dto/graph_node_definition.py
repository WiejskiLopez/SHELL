from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class GraphNodeDefinitionDto:
    id: str
    position: int
    mode: str
    role: str
    node_type: str
    model: str
    command: str
    timeout: int = 0
    retries: int = 0
    log_level: str = "INFO"
    max_step: int | None = None
    no_ask_user: bool = False
    autopilot: bool = False
    status_initial: str = ""
    script: str = ""
    script_type: str = ""
