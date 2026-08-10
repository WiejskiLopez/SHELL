from __future__ import annotations

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from shell.platform.framework.api.principal import (
    Principal,
    PrincipalKind,
    get_principal,
    require_user_principal,
)


def _request(principal: Principal | None) -> Request:
    state = {} if principal is None else {"principal": principal}
    return Request({"type": "http", "state": state})


def test_get_principal_fails_closed_without_principal() -> None:
    with pytest.raises(HTTPException) as error:
        get_principal(_request(None))

    assert error.value.status_code == 401


def test_require_user_principal_rejects_system_principal() -> None:
    with pytest.raises(HTTPException) as error:
        require_user_principal(_request(Principal(subject_id="system", kind=PrincipalKind.SYSTEM)))

    assert error.value.status_code == 403


def test_require_user_principal_returns_user_principal() -> None:
    principal = Principal(subject_id="user-1", kind=PrincipalKind.USER)

    assert require_user_principal(_request(principal)) == principal
