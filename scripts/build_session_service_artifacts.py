#!/usr/bin/env python
"""Build the independent platform and Session BC wheels."""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts.build_user_service_artifacts import (
    REPOSITORY_ROOT,
    build_service_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPOSITORY_ROOT / "dist" / "session-service",
    )
    args = parser.parse_args()
    build_service_artifacts(
        service_name="session_service",
        service_package_name="shell-session-service",
        output_dir=args.output_dir.resolve(),
    )


if __name__ == "__main__":
    main()