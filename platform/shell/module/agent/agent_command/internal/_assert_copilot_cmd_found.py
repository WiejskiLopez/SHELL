"""_assert_copilot_cmd_found.py
Responsible for one thing: raising FileNotFoundError when the agent CLI binary cannot be located.
"""


def _assert_copilot_cmd_found(command) -> None:
    """Raise FileNotFoundError if command is falsy."""
    if not command:
        raise FileNotFoundError(
            "Agent CLI not found. Set command in app/app.yaml "
            "or ensure the binary is on PATH."
        )
