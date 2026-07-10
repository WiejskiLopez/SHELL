from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column


class VersionedMixin:
    """Dodaje kolumnę ``version`` z auto-inkrementacją przez ``version_id_col``.

    Każda klasa modelu która dziedziczy ten mixin MUSI ustawić
    ``__mapper_args__`` z referencją do w pełni skonfigurowanej kolumny
    (przez ``@declared_attr``) — SQLAlchemy nie dziedziczy
    ``__mapper_args__`` po mixinach.
    """

    version: Mapped[int] = mapped_column(
        "version",
        nullable=False,
        default=1,
    )
