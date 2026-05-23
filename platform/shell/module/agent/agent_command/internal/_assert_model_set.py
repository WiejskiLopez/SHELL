"""_assert_model_set.py
Responsible for one thing: raising ValueError when model app field is missing.
"""


def _assert_model_set(model: str) -> None:
    """Raise ValueError if model is empty."""
    if not model:
        raise ValueError("[build_command] Required app field missing: 'model'")
