def _assert_session_id_set(session_id: str | None) -> None:
    if session_id is None:
        raise RuntimeError('session_id is not set — call _init_task_yaml before accessing session_id_')
