def _assert_router_base_set(value) -> None:
    if value is None:
        raise ValueError("router_base not initialized — call init_router() first")
