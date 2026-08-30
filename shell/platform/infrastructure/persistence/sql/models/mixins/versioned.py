from __future__ import annotations

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class VersionedMixin:
    """Adds a ``version`` column (Integer) with auto-increment via ``version_id_col``.

    Every model class inheriting this mixin MUST set ``__mapper_args__``
    with a reference to the fully configured column (via ``@declared_attr``).
    SQLAlchemy does not inherit ``__mapper_args__`` from mixins.
    """

    version: Mapped[int] = mapped_column(
        Integer,
        name="version",
        nullable=False,
        default=1,
    )

    @declared_attr  # type: ignore[arg-type]
    def __mapper_args__(cls) -> dict[str, object]:
        return {"version_id_col": cls.version}
