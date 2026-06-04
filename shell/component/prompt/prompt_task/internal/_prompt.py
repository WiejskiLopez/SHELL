def _prompt(prompt_task) -> str:
    sorted_prompts = sorted(prompt_task._file_prompts, key=lambda p: p._file_name)
    return "\n\n".join(p._file_body for p in sorted_prompts if p._file_body)
