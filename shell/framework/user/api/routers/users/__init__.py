from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request as _Request

from shell.domain.user.value_objects.user_id import UserId

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer
    from shell.domain.user.ports.user_acl import UserACL

router = APIRouter(prefix="/users", tags=["users"])


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


@router.get("/{user_id}")
async def get_user(
    user_id: str,
    container: CoreContainer = Depends(get_core_container),
) -> dict:
    _user_acl: UserACL | None = getattr(container.infra, "user_acl_factory", None)
    if _user_acl is None:
        raise HTTPException(status_code=501, detail="User ACL not implemented")
    result = await _user_acl.get_user(UserId(user_id))
    if result is None:
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
    return {"id": user_id, "user": str(result)}
