"""Compatibility wrapper for the shared SHELL certificate generator."""

from __future__ import annotations

import argparse
from pathlib import Path

from shell.certificates import generate_bundle

ROOT = Path(__file__).resolve().parents[1]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "shell" / "certs")
    parser.add_argument("--force", action="store_true")
    arguments = parser.parse_args()
    generate_bundle(arguments.output_dir, force=arguments.force)
    print(f"Generated mTLS certificate bundle in {arguments.output_dir}")
