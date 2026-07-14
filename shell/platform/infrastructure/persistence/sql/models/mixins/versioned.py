from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column


class VersionedMixin:
    """Adds a ``version`` column with auto-increment via ``version_id_col``.

    Every model class inheriting this mixin MUST set ``__mapper_args__``
    with a reference to the fully configured column (via ``@declared_attr``).
    SQLAlchemy does not inherit ``__mapper_args__`` from mixins.
    """

    version: Mapped[int] = mapped_column(
        "version",
        nullable=False,
        default=1,
    )
