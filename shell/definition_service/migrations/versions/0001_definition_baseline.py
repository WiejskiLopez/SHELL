from __future__ import annotations

from alembic import op

from shell.platform.infrastructure.persistence.service_schema_migration import (
    create_service_tables,
    drop_service_tables,
)

revision = "0001_definition_baseline"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    create_service_tables(
        op.get_bind(),
        service_package="shell.definition_service",
        base_module="shell.definition_service.infrastructure.definition.persistence.sql.models.base",
        base_class="DefinitionSqlAlchemyModelBase",
    )


def downgrade() -> None:
    drop_service_tables(
        op.get_bind(),
        service_package="shell.definition_service",
        base_module="shell.definition_service.infrastructure.definition.persistence.sql.models.base",
        base_class="DefinitionSqlAlchemyModelBase",
    )
