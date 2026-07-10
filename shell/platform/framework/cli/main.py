"""Main CLI entrypoint for shell — dispatches to per-mode command handlers."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry-point — first positional arg is the mode/subcommand."""
    arguments = list(argv) if argv is not None else sys.argv[1:]
    if not arguments:
        print("Usage: shell <mode> [options]", file=sys.stderr)
        return 1

    mode = arguments[0]
    print(f"Unknown mode: {mode!r}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
