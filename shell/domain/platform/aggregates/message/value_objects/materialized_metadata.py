from __future__ import annotations

from dataclasses import dataclass, field

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class MaterializedMetadata(ValueObject):
    workflow_id: str = ""
    step: int = 0
    sequence_id: int = 0
    source_node_execution_id: str = ""
    target_node_execution_id: str = ""
    source_role: str = ""
    target_role: str = ""

    def __bool__(self) -> bool:
        return bool(self.workflow_id)

    def to_dict(self) -> dict[str, object]:
        return {
            "workflow_id": self.workflow_id,
            "step": self.step,
            "sequence_id": self.sequence_id,
            "source_node_execution_id": self.source_node_execution_id,
            "target_node_execution_id": self.target_node_execution_id,
            "source_role": self.source_role,
            "target_role": self.target_role,
        }
