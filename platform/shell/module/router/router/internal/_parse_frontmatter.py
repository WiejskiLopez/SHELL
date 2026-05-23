"""_parse_frontmatter.py
Responsible for one thing: parsing YAML front-matter from text.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

import yaml


def _parse_frontmatter(text: str) -> Tuple[Optional[Dict], str]:
    """Parse YAML front-matter. Returns (data, body) or (None, text) on parse failure."""
    if not text.startswith("---"):
        return None, text
    end = text.find("\n---", 3)
    if end == -1:
        return None, text
    fm_text = text[3:end].strip()
    body = text[end + 4:]
    try:
        data = yaml.safe_load(fm_text)
        return data, body
    except yaml.YAMLError:
        return None, text
