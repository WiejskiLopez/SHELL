"""${message}"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

${up_revision = repr(up_revision)}
${down_revision = repr(down_revision)}
${branch_labels = repr(branch_labels)}
${depends_on = repr(depends_on)}


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass