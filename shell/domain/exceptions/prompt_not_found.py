from shell.domain.exceptions._base import DomainError


class PromptNotFound(DomainError):
    def __init__(self, name: str) -> None:
        super().__init__(f"Prompt not found: {name!r}")
