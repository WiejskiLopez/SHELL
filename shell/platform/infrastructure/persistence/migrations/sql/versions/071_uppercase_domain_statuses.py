"""Move domain status codes to uppercase and remove database defaults.

Revision ID: 071
Revises: 070
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "071"
down_revision = "070"
branch_labels = None
depends_on = None

_STATUS_TABLES = (
    ("graph_execution", "created", "PENDING", "created"),
    ("node_execution", "pending", "PENDING", "pending"),
    ("task_execution", "created", "CREATED", "created"),
    ("workflow", "idle", "ACTIVE", "idle"),
    ("project", "active", "ACTIVE", "active"),
    ("scheduler_job", "pending", "PENDING", "pending"),
    ("session", "open", "OPEN", "open"),
    ("user", "active", "ACTIVE", "active"),
)


def _normalize_statuses() -> None:
    for table_name, legacy_value, normalized_value, _ in _STATUS_TABLES:
        quoted_table_name = f'"{table_name}"'
        op.execute(
            sa.text(
                f"UPDATE {quoted_table_name} "
                "SET status = CASE "
                f"WHEN LOWER(status) = :legacy_value THEN :normalized_value "
                "ELSE UPPER(status) END"
            ).bindparams(
                legacy_value=legacy_value,
                normalized_value=normalized_value,
            )
        )


def _alter_status_defaults(server_defaults: dict[str, str | None]) -> None:
    for table_name, _, _, _ in _STATUS_TABLES:
        with op.batch_alter_table(table_name) as batch:
            batch.alter_column(
                "status",
                existing_type=sa.String(50),
                server_default=server_defaults[table_name],
            )


def upgrade() -> None:
    _normalize_statuses()
    _alter_status_defaults({table_name: None for table_name, _, _, _ in _STATUS_TABLES})


def downgrade() -> None:
    _alter_status_defaults(
        {table_name: legacy_default for table_name, _, _, legacy_default in _STATUS_TABLES}
    )
    for table_name, _, _, _ in _STATUS_TABLES:
        op.execute(sa.text(f'UPDATE "{table_name}" SET status = LOWER(status)'))
