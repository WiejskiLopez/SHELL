from __future__ import annotations

from datetime import UTC, datetime

from shell.definition_service.domain.definition.aggregates.graph_definition.graph_definition import (
    GraphDefinition,
)
from shell.definition_service.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt


class TestGraphDefinition:
    def test_create_graph_definition(self) -> None:
        gd = GraphDefinition(
            id=GraphDefinitionId("gd-2"),
            created_at=CreatedAt.from_datetime(datetime.now(tz=UTC)),
        )
        assert gd.id.value == "gd-2"
