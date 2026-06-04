"""_assert_prompt_not_empty.py
Responsible for one thing: raising ValueError when prompt is empty.
"""


def _assert_prompt_not_empty(prompt: str) -> None:
    """Raise ValueError if prompt is falsy."""
    if not prompt:
        raise ValueError("[_run_agent] prompt is required and cannot be empty")
