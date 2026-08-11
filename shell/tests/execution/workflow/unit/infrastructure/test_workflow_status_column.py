from sqlalchemy import String

from shell.execution.infrastructure.execution.workflow.persistence.sql.models import WorkflowModel


def test_workflow_status_column_is_limited_to_50_characters() -> None:
    status_column = WorkflowModel.__table__.c.status

    assert isinstance(status_column.type, String)
    assert status_column.type.length == 50
    assert status_column.default is None
    assert status_column.server_default is None
