def _assert_command_set(command: list | None) -> None:
    if command is None:
        raise ValueError("[AgentCommand] command_ accessed before init_agent_command() was called")
