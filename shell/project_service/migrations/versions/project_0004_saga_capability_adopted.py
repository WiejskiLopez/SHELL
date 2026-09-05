"""Adopt platform-created saga tables as project-service capability tables."""

from __future__ import annotations

from alembic import op
from sqlalchemy import inspect

revision = "project_0004_saga_capability_adopted"
down_revision = "project_0003_project_state"
branch_labels = None
depends_on = None

_REQUIRED_TABLES = frozenset({"saga_instance", "saga_timeout"})


def upgrade() -> None:
    connection = op.get_bind()
    existing_tables = set(inspect(connection).get_table_names())
    missing_tables = _REQUIRED_TABLES - existing_tables
    if missing_tables:
        missing = ", ".join(sorted(missing_tables))
        raise RuntimeError(f"Cannot adopt missing saga tables: {missing}")


def downgrade() -> None:
    """Keep adopted tables intact; ownership rollback must not drop saga state."""
