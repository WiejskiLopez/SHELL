"""entrypoint.py
Entry point for tasker-worker.
Contains ONLY method calls — no inline logic.

Exit codes for the external orchestrator:
    0 — success
    1 — error
    2 — timeout
    4 — locked
    5 — question
"""

import sys

from shell.app.app import App


def main() -> int:
    app = App.init_app(mode='tasker', runner_root_dir=__file__)
    return app.run_app()

if __name__ == "__main__":
    sys.exit(main())
