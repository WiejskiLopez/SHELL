"""Koncept: reguła architektoniczna dotycząca database metadata isolation: test each bc has distinct metadata with only its tables.

Reguła: test sprawdza kontrakt architektoniczny database metadata isolation: test each bc has distinct metadata with only its tables.

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


def test_each_bc_has_distinct_metadata_with_only_its_tables() -> None:
    for module_name in _BASELINE_MODULES:
        import_module(module_name)
    metadata_by_bc = {
        bounded_context: _load_base(base_path).metadata
        for bounded_context, base_path in _BASES.items()
    }
    for _bounded_context, metadata in metadata_by_bc.items():
        assert {"event_inbox", "event_outbox"}.issubset(metadata.tables), (
            architecture_assertion_message(
                "reguła testowana przez test_each_bc_has_distinct_metadata_with_only_its_tables",
                "warunek zapisany w asercji musi być spełniony",
                "Asercja nie zawierała dodatkowych szczegółów.",
            )
        )
    assert len({id(metadata) for metadata in metadata_by_bc.values()}) == len(_BASES), (
        architecture_assertion_message(
            "reguła testowana przez test_each_bc_has_distinct_metadata_with_only_its_tables",
            "warunek zapisany w asercji musi być spełniony",
            "Asercja nie zawierała dodatkowych szczegółów.",
        )
    )
