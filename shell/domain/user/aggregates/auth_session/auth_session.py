"""AuthSession — login session aggregate root.

Owns the lifecycle of an authentication session (created -> revoked/expired).
The raw token is never stored; only its SHA-256 hash is kept on the aggregate.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Self

from shell.domain.user.aggregates.auth_session.events.auth_session_created_event import (
    AuthSessionCreatedEvent,
)
from shell.domain.user.aggregates.auth_session.events.auth_session_deleted_event import (
    AuthSessionDeletedEvent,
)
from shell.domain.user.aggregates.auth_session.events.auth_session_revoked_event import (
    AuthSessionRevokedEvent,
)
from shell.domain.user.aggregates.auth_session.events.auth_session_updated_event import (
    AuthSessionUpdatedEvent,
)
from shell.domain.user.aggregates.auth_session.value_objects.auth_session_id import (
    AuthSessionId,
)
from shell.domain.user.aggregates.auth_session.value_objects.revoked_at import (
    NONE_REVOKED_AT,
    RevokedAt,
)
from shell.platform.domain.base.aggregate_root import AggregateRoot
from shell.platform.domain.exceptions.domain_error import DomainError
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import NONE_DELETED_AT, DeletedAt
from shell.platform.domain.value_objects.occurred_at import OccurredAt
from shell.platform.domain.value_objects.updated_at import NONE_UPDATED_AT, UpdatedAt

if TYPE_CHECKING:
    from shell.domain.user.aggregates.auth_session.value_objects.expires_at import ExpiresAt
    from shell.domain.user.value_objects.user_id import UserId
    from shell.platform.domain.value_objects.hash import Hash


class AuthSession(AggregateRoot[AuthSessionId]):
    __slots__ = (
        "_created_at",
        "_updated_at",
        "_deleted_at",
        "_user_id",
        "_token_hash",
        "_expires_at",
        "_revoked_at",
    )

    _user_id: UserId
    _token_hash: Hash
    _expires_at: ExpiresAt
    _revoked_at: RevokedAt
    _created_at: CreatedAt
    _updated_at: UpdatedAt
    _deleted_at: DeletedAt

    def __init__(
        self,
        *,
        id: AuthSessionId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        user_id: UserId,
        token_hash: Hash,
        expires_at: ExpiresAt,
        revoked_at: RevokedAt = NONE_REVOKED_AT,
    ) -> None:
        super().__init__(id)
        self._user_id = user_id
        self._token_hash = token_hash
        self._expires_at = expires_at
        self._revoked_at = revoked_at
        self._created_at = created_at
        self._updated_at = updated_at
        self._deleted_at = deleted_at

    @classmethod
    def _new(
        cls,
        *,
        id_: AuthSessionId,
        now: OccurredAt,
        user_id: UserId,
        token_hash: Hash,
        expires_at: ExpiresAt,
    ) -> AuthSession:
        auth_session = cls(
            id=id_,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            created_at=CreatedAt.from_datetime(now.value),
        )
        auth_session.append_event(
            AuthSessionCreatedEvent.now(
                auth_session_id=auth_session.id,
                user_id=user_id,
                now=now,
            )
        )
        return auth_session

    @classmethod
    def create(
        cls,
        *,
        id_: AuthSessionId,
        now: CreatedAt,
        user_id: UserId,
        token_hash: Hash,
        expires_at: ExpiresAt,
    ) -> AuthSession:
        return cls._new(
            id_=id_,
            now=OccurredAt.from_datetime(now.value),
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

    @classmethod
    def restore(
        cls,
        *,
        id: AuthSessionId,
        created_at: CreatedAt,
        updated_at: UpdatedAt = NONE_UPDATED_AT,
        deleted_at: DeletedAt = NONE_DELETED_AT,
        user_id: UserId,
        token_hash: Hash,
        expires_at: ExpiresAt,
        revoked_at: RevokedAt = NONE_REVOKED_AT,
    ) -> Self:
        return cls(
            id=id,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            revoked_at=revoked_at,
            created_at=created_at,
            updated_at=updated_at,
            deleted_at=deleted_at,
        )

    def _update(self, now: UpdatedAt) -> None:
        self._updated_at = now
        self.append_event(
            AuthSessionUpdatedEvent.now(
                auth_session_id=self._id,
                user_id=self._user_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def _delete(self, now: DeletedAt) -> None:
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            AuthSessionDeletedEvent.now(
                auth_session_id=self._id,
                user_id=self._user_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def update(self, now: UpdatedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Cannot update a deleted auth session")
        self._updated_at = now
        self.append_event(
            AuthSessionUpdatedEvent.now(
                auth_session_id=self._id,
                user_id=self._user_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def delete(self, now: DeletedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Auth session already deleted")
        self._deleted_at = now
        self._updated_at = UpdatedAt.from_datetime(now.value)
        self.append_event(
            AuthSessionDeletedEvent.now(
                auth_session_id=self._id,
                user_id=self._user_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def renew_token(self, token_hash: Hash, now: UpdatedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Cannot renew token of a deleted auth session")
        if self._revoked_at.value is not None:
            raise DomainError("Cannot renew token of a revoked auth session")
        self._token_hash = token_hash
        self._updated_at = now
        self.append_event(
            AuthSessionUpdatedEvent.now(
                auth_session_id=self._id,
                user_id=self._user_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    def revoke(self, now: UpdatedAt) -> None:
        if self._deleted_at.value is not None:
            raise DomainError("Cannot revoke a deleted auth session")
        if self._revoked_at.value is not None:
            raise DomainError("Auth session already revoked")
        self._revoked_at = RevokedAt.from_datetime(now.value)
        self._updated_at = now
        self.append_event(
            AuthSessionRevokedEvent.now(
                auth_session_id=self._id,
                user_id=self._user_id,
                now=OccurredAt.from_datetime(now.value),
            )
        )

    @property
    def user_id(self) -> UserId:
        return self._user_id

    @property
    def token_hash(self) -> Hash:
        return self._token_hash

    @property
    def expires_at(self) -> ExpiresAt:
        return self._expires_at

    @property
    def revoked_at(self) -> RevokedAt:
        return self._revoked_at

    @property
    def created_at(self) -> CreatedAt:
        return self._created_at

    @property
    def updated_at(self) -> UpdatedAt:
        return self._updated_at

    @property
    def deleted_at(self) -> DeletedAt:
        return self._deleted_at

    @property
    def is_deleted(self) -> bool:
        return self._deleted_at.value is not None
