def _prompt(prompt_system) -> str:
    sorted_prompts = sorted(prompt_system._file_prompts, key=lambda p: p._file_name)
    return "\n\n".join(p._file_body for p in sorted_prompts if p._file_body)
