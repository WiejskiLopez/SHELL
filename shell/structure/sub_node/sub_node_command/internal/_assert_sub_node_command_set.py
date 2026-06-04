def _assert_sub_node_command_set(command) -> None:
    if command is None:
        raise ValueError("[SubNodeCommand] _command is not set — call init_sub_node_command() first")
