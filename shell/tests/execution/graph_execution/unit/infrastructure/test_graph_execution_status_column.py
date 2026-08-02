from sqlalchemy import String

from shell.infrastructure.execution.graph_execution.persistence.sql.models import (
    GraphExecutionModel,
)


def test_graph_execution_status_column_is_limited_to_50_characters() -> None:
    status_column = GraphExecutionModel.__table__.c.status

    assert isinstance(status_column.type, String)
    assert status_column.type.length == 50
    assert status_column.default is None
    assert status_column.server_default is None
