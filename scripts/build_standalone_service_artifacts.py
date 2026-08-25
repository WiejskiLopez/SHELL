#!/usr/bin/env python
"""Build an independently packaged bounded-context service."""

from __future__ import annotations

import argparse
from pathlib import Path

from scripts.build_user_service_artifacts import build_service_artifacts

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--service", required=True)
    parser.add_argument("--package", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    build_service_artifacts(
        service_name=args.service,
        service_package_name=args.package,
        output_dir=args.output_dir.resolve(),
    )


if __name__ == "__main__":
    main()