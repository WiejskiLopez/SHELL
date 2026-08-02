"""Add unique constraint to user.email and deduplicate existing rows.

Revision ID: 069
Revises: 068
Create Date: 2026-08-02

* Backfill duplicate ``email`` values so every row is unique
* Add a unique constraint on ``user.email``
"""

from __future__ import annotations

from alembic import op

revision = "069"
down_revision = "068"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Keep the lowest-id row per email, rewrite the rest to an id-based email
    # (id is unique, so id || '@duplicate.invalid' is guaranteed unique).
    op.execute(
        'UPDATE "user" '
        "SET email = id || '@duplicate.invalid' "
        'WHERE id NOT IN (SELECT MIN(id) FROM "user" GROUP BY email)'
    )
    with op.batch_alter_table("user") as batch:
        batch.create_unique_constraint("uq_user_email", ["email"])


def downgrade() -> None:
    with op.batch_alter_table("user") as batch:
        batch.drop_constraint("uq_user_email", type_="unique")
