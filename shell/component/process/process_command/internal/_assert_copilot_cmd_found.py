def _assert_copilot_cmd_found(command) -> None:
    if not command:
        raise FileNotFoundError(
            "Agent CLI not found. Set command in app/app.yaml "
            "or ensure the binary is on PATH."
        )
