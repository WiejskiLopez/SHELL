from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.hash import Hash
from shell.user.domain.user.aggregates.auth_session.auth_session import AuthSession
from shell.user.domain.user.aggregates.auth_session.value_objects.auth_session_id import (
    AuthSessionId,
)
from shell.user.domain.user.aggregates.auth_session.value_objects.expires_at import ExpiresAt
from shell.user.domain.user.value_objects.user_id import UserId
from shell.user.infrastructure.user.auth_session.persistence.memory.in_memory_auth_session_repository import (
    InMemoryAuthSessionRepository,
)


@pytest.mark.asyncio
async def test_get_active_by_user_id_excludes_expired_sessions() -> None:
    now = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    repository = InMemoryAuthSessionRepository()
    user_id = UserId("user-1")

    active_session = AuthSession.create(
        id_=AuthSessionId("active-session"),
        now=CreatedAt.from_datetime(now),
        user_id=user_id,
        token_hash=Hash.of("active-token"),
        expires_at=ExpiresAt.from_datetime(now + timedelta(minutes=1)),
    )
    expired_session = AuthSession.create(
        id_=AuthSessionId("expired-session"),
        now=CreatedAt.from_datetime(now),
        user_id=user_id,
        token_hash=Hash.of("expired-token"),
        expires_at=ExpiresAt.from_datetime(now - timedelta(seconds=1)),
    )
    await repository.save(active_session)
    await repository.save(expired_session)

    result = await repository.get_active_by_user_id(user_id, CreatedAt.from_datetime(now))

    assert result is active_session


@pytest.mark.asyncio
async def test_get_active_by_user_id_returns_none_when_only_session_is_expired() -> None:
    now = datetime(2026, 8, 10, 12, 0, tzinfo=UTC)
    repository = InMemoryAuthSessionRepository()
    session = AuthSession.create(
        id_=AuthSessionId("expired-session"),
        now=CreatedAt.from_datetime(now - timedelta(hours=1)),
        user_id=UserId("user-1"),
        token_hash=Hash.of("expired-token"),
        expires_at=ExpiresAt.from_datetime(now - timedelta(seconds=1)),
    )
    await repository.save(session)

    result = await repository.get_active_by_user_id(UserId("user-1"), CreatedAt.from_datetime(now))

    assert result is None
