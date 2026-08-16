from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.base.value_object import ValueObject

if TYPE_CHECKING:
    from shell.user_service.domain.user.value_objects.user_id import UserId
    from shell.user_service.domain.user.value_objects.user_status import UserStatus


@dataclass(frozen=True, slots=True)
class UserReference(ValueObject):
    """Minimal read model of a User consumed by the AuthSession aggregate."""

    id: UserId
    status: UserStatus
