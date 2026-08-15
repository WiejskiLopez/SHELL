"""Architecture tests for bounded-context database metadata ownership."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase


_BASES = {
    "definition": "shell.definition.infrastructure.definition.persistence.sql.models.base.DefinitionSqlAlchemyModelBase",
    "execution": "shell.execution.infrastructure.execution.persistence.sql.models.base.ExecutionSqlAlchemyModelBase",
    "ingestion": "shell.ingestion.infrastructure.ingestion.persistence.sql.models.base.IngestionSqlAlchemyModelBase",
    "project": "shell.project.infrastructure.project.persistence.sql.models.base.ProjectSqlAlchemyModelBase",
    "scheduling": "shell.scheduling.infrastructure.scheduling.persistence.sql.models.base.SchedulingSqlAlchemyModelBase",
    "session": "shell.session.infrastructure.session.persistence.sql.models.base.SessionSqlAlchemyModelBase",
    "user": "shell.user.infrastructure.user.persistence.sql.models.base.UserSqlAlchemyModelBase",
}

_BASELINE_MODULES = tuple(
    f"shell.{bounded_context}.migrations.baseline" for bounded_context in _BASES
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
        assert {"inbox_event", "outbox_event"}.issubset(metadata.tables)

    assert len({id(metadata) for metadata in metadata_by_bc.values()}) == len(_BASES)


def test_each_bc_uses_distinct_event_delivery_table_objects() -> None:
    from shell.platform.infrastructure.persistence.sql.models.base import SqlAlchemyModelBase

    for module_name in _BASELINE_MODULES:
        import_module(module_name)

    platform_tables = SqlAlchemyModelBase.metadata.tables
    assert not {"inbox_event", "outbox_event"}.intersection(platform_tables)
    for base_path in _BASES.values():
        metadata = _load_base(base_path).metadata
        assert metadata.tables["inbox_event"] not in platform_tables.values()
        assert metadata.tables["outbox_event"] not in platform_tables.values()
