"""Drop V1 orphaned tables (envelope, envelope_event, envelope_archive, node_state).

Revision ID: 053
Revises: 052
Create Date: 2026-07-05

Changes:
* Drop ``envelope`` table (V1 artifact, no ORM model, no code references)
* Drop ``envelope_event`` table (V1 artifact, no ORM model, no code references)
* Drop ``envelope_archive`` table (V1 artifact, no ORM model, no code references)
* Drop ``node_state`` table (V1 artifact, no ORM model, no code references)
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "053"
down_revision = "052"


def upgrade() -> None:
    op.drop_table("node_state")
    op.drop_table("envelope_archive")
    op.drop_table("envelope_event")
    op.drop_table("envelope")


def downgrade() -> None:
    op.create_table(
        "envelope",
        sa.Column("id", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "envelope_event",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("envelope_id", sa.String(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("event", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "envelope_archive",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("envelope_id", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "node_state",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("node_execution_id", sa.String(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
