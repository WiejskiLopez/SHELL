from __future__ import annotations


class ValueObject:
    """Base class for all domain value objects.

    Value objects are immutable and compared by their structural contents
    (all fields), not by identity.  Concrete subclasses are expected to be
    ``@dataclass(frozen=True)`` or ``StrEnum`` — the frozen dataclass provides
    ``__eq__``, ``__hash__``, ``__repr__`` and ``__slots__`` automatically.

    Example::

        @dataclass(frozen=True, slots=True)
        class Status(ValueObject):
            value: str

            def __post_init__(self) -> None:
                if not self.value:
                    raise ValueError("Status cannot be empty")
    """
