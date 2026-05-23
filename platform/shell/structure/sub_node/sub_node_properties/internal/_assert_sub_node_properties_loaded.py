def _assert_sub_node_properties_loaded(name: str | None) -> None:
    if name is None:
        raise ValueError("[SubNodeProperties] not loaded — call init_sub_node_properties() first")
