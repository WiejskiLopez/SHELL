"""Koncept: reguła architektoniczna dotycząca database metadata isolation: test each bc uses distinct event delivery table objects.

Reguła: test sprawdza kontrakt architektoniczny database metadata isolation: test each bc uses distinct event delivery table objects.

Poprawnie: kod spełnia ten kontrakt i nie zgłasza naruszeń.
"""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, cast

from _arch_helpers import architecture_assertion_message

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase
_BASES = {
    "definition": "shell.definition_service.infrastructure.definition.persistence.sql.models.base.DefinitionSqlAlchemyModelBase",
    "execution": "shell.execution_service.infrastructure.execution.persistence.sql.models.base.ExecutionSqlAlchemyModelBase",
    "ingestion": "shell.ingestion_service.infrastructure.ingestion.persistence.sql.models.base.IngestionSqlAlchemyModelBase",
    "project": "shell.project_service.infrastructure.project.persistence.sql.models.base.ProjectSqlAlchemyModelBase",
    "scheduling": "shell.scheduling_service.infrastructure.scheduling.persistence.sql.models.base.SchedulingSqlAlchemyModelBase",
    "session": "shell.session_service.infrastructure.session.persistence.sql.models.base.SessionSqlAlchemyModelBase",
    "user": "shell.user_service.infrastructure.user.persistence.sql.models.base.UserSqlAlchemyModelBase",
}
_BASELINE_MODULES = tuple(
    f"shell.{bounded_context}_service.migrations.baseline" for bounded_context in _BASES
)


def _load_base(path: str) -> type[DeclarativeBase]:
    module_name, class_name = path.rsplit(".", maxsplit=1)
    return cast("type[DeclarativeBase]", getattr(import_module(module_name), class_name))


def test_each_bc_uses_distinct_event_delivery_table_objects() -> None:
    from shell.platform.infrastructure.persistence.sql.models.base import SqlAlchemyModelBase

    for module_name in _BASELINE_MODULES:
        import_module(module_name)
    platform_tables = SqlAlchemyModelBase.metadata.tables
    assert not {"inbox_event", "outbox_event"}.intersection(platform_tables), (
        architecture_assertion_message(
            "reguła testowana przez test_each_bc_uses_distinct_event_delivery_table_objects",
            "warunek zapisany w asercji musi być spełniony",
            "Asercja nie zawierała dodatkowych szczegółów.",
        )
    )
    for base_path in _BASES.values():
        metadata = _load_base(base_path).metadata
        assert metadata.tables["inbox_event"] not in platform_tables.values(), (
            architecture_assertion_message(
                "reguła testowana przez test_each_bc_uses_distinct_event_delivery_table_objects",
                "warunek zapisany w asercji musi być spełniony",
                "Asercja nie zawierała dodatkowych szczegółów.",
            )
        )
        assert metadata.tables["outbox_event"] not in platform_tables.values(), (
            architecture_assertion_message(
                "reguła testowana przez test_each_bc_uses_distinct_event_delivery_table_objects",
                "warunek zapisany w asercji musi być spełniony",
                "Asercja nie zawierała dodatkowych szczegółów.",
            )
        )
