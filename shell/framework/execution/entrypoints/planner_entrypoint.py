from __future__ import annotations

import sys

from shell.framework.platform.cli.main import main

if __name__ == "__main__":
    sys.exit(main(["planner", *sys.argv[1:]]))
