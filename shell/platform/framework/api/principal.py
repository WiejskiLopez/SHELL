from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from fastapi import HTTPException, Request, status


class PrincipalKind(StrEnum):
    USER = "user"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class Principal:
    subject_id: str
    kind: PrincipalKind


SYSTEM_SUBJECT_ID = "system"


def get_principal(request: Request) -> Principal:
    principal = getattr(request.state, "principal", None)
    if not isinstance(principal, Principal):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication",
        )
    return principal


def require_user_principal(request: Request) -> Principal:
    principal = get_principal(request)
    if principal.kind != PrincipalKind.USER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User authentication required",
        )
    return principal


def require_system_principal(request: Request) -> Principal:
    principal = get_principal(request)
    if principal.kind != PrincipalKind.SYSTEM:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="System authentication required",
        )
    return principal
