"""Command-line entrypoint for the shared SHELL certificate generator."""

from __future__ import annotations

import argparse
from pathlib import Path

from shell.certificates.generator import generate_bundle

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output-dir", type=Path, required=True)
parser.add_argument("--force", action="store_true")
args = parser.parse_args()
generate_bundle(args.output_dir, force=args.force)
print(f"Generated mTLS certificate bundle in {args.output_dir}")
