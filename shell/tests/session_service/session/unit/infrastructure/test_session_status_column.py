from sqlalchemy import String

from shell.session_service.infrastructure.session.session.persistence.sql.models import SessionModel


def test_session_status_column_is_limited_to_50_characters() -> None:
    status_column = SessionModel.__table__.c.status

    assert isinstance(status_column.type, String)
    assert status_column.type.length == 50
    assert status_column.default is None
    assert status_column.server_default is None
