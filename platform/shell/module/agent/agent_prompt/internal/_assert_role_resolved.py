def _assert_role_resolved(role) -> None:
    if role is None:
        raise ValueError("role is not set — required for prompt_role loading")
