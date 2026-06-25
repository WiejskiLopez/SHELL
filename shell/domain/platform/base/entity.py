from __future__ import annotations

from abc import ABC
from typing import Generic, TypeVar

TId = TypeVar("TId")


class Entity(ABC, Generic[TId]):
    """Base class for all domain entities.

    Identity is opaque (``TId``) and immutable after construction.
    Equality and hashing are based exclusively on identity, never on field
    contents. Two entities with the same identity ARE the same entity,
    regardless of their state.
    """

    __slots__ = ("_id", "_version")

    _id: TId
    _version: int

    def __init__(self, id: TId) -> None:
        self._id = id
        self._version = 0

    @property
    def id(self) -> TId:
        return self._id

    @property
    def version(self) -> int:
        return self._version

    def _increment_version(self) -> None:
        self._version += 1

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity):
            return NotImplemented
        return bool(self._id == other._id)

    def __hash__(self) -> int:
        return hash(self._id)
