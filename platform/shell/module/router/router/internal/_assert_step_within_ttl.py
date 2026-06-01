from shell.module.router.router.parse_message_filename import MessageFilename


def _assert_step_within_ttl(parsed: MessageFilename, max_step: int) -> None:
    try:
        step = int(parsed.step)
    except (ValueError, TypeError):
        return
    if step >= max_step:
        raise RuntimeError(
            f"TTL exceeded: message '{parsed.sequence_id}__{parsed.from_role}__{parsed.to_role}' "
            f"has step={step} >= max_step={max_step}"
        )
