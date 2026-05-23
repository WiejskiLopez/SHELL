import re


def _assert_no_unresolved_placeholders(text: str) -> None:
    unresolved = re.findall(r'\$\$[^$]+\$\$', text)
    if unresolved:
        raise ValueError(f"Unresolved placeholders in prompt text: {unresolved}")
