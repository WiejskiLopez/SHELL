from sqlalchemy import String

from shell.execution.infrastructure.execution.node_execution.persistence.sql.models import (
    NodeExecutionModel,
    NodeExecutionResultModel,
)


def test_node_execution_status_column_is_limited_to_50_characters() -> None:
    status_column = NodeExecutionModel.__table__.c.status

    assert isinstance(status_column.type, String)
    assert status_column.type.length == 50
    assert status_column.default is None
    assert status_column.server_default is None


def test_node_execution_result_status_column_is_limited_to_50_characters() -> None:
    status_column = NodeExecutionResultModel.__table__.c.status

    assert isinstance(status_column.type, String)
    assert status_column.type.length == 50
