from sqlalchemy import String

from shell.infrastructure.scheduling.scheduler_job.persistence.sql.models import SchedulerJobModel


def test_scheduler_job_status_column_is_limited_to_50_characters() -> None:
    status_column = SchedulerJobModel.__table__.c.status

    assert isinstance(status_column.type, String)
    assert status_column.type.length == 50
    assert status_column.default is None
    assert status_column.server_default is None
