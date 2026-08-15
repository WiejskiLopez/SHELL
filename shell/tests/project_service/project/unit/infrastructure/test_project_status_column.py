from sqlalchemy import String

from shell.project_service.infrastructure.project.project.persistence.sql.models import ProjectModel


def test_project_status_column_is_limited_to_50_characters() -> None:
    status_column = ProjectModel.__table__.c.status

    assert isinstance(status_column.type, String)
    assert status_column.type.length == 50
    assert status_column.default is None
    assert status_column.server_default is None
