def _assert_db_node_port_set(value, name: str) -> None:
    if value is None:
        raise ValueError(f"DbNodePort.{name} not set — call init_db_node_port() first")
