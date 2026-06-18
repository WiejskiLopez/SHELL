from shell.domain.exceptions._base import DomainError


class TaskExecutionNotFound(DomainError):
    def __init__(self, id: str) -> None:
        super().__init__(f"Task not found: {id!r}")
