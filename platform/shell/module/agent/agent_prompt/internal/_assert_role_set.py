def _assert_role_set(role) -> None:
    if not role:
        raise ValueError("[init_system_prompt] 'role' is required in app but was not set.")
