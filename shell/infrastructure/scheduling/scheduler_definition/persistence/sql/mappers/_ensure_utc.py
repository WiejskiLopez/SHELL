import json
from datetime import UTC, datetime

from shell.domain.scheduling.aggregates.scheduler_definition.scheduler_definition import (
    SchedulerDefinition,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.action_config import (
    ActionConfig,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.execution_policy import (
    ExecutionPolicy,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_description import (
    SchedulerDescription,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_name import (
    SchedulerName,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.trigger_config import (
    TriggerConfig,
)
from shell.infrastructure.scheduling.scheduler_definition.persistence.sql.models.scheduler_definition import (
    SchedulerDefinitionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.enabled import Enabled
from shell.platform.domain.value_objects.timestamp import Timestamp
from shell.platform.types import JsonStr


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt

