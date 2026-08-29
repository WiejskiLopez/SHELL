"""Command-line interface for shared SHELL certificate infrastructure."""

from __future__ import annotations

import argparse
from pathlib import Path

from shell.certificates.generator import ensure_ca, generate_bundle, issue_certificate

parser = argparse.ArgumentParser(description=__doc__)
commands = parser.add_subparsers(dest="command", required=True)

ensure_command = commands.add_parser("ensure-ca")
ensure_command.add_argument("--ca-dir", type=Path, required=True)
ensure_command.add_argument("--lifetime-days", type=int, default=1825)
ensure_command.add_argument("--force", action="store_true")

issue_command = commands.add_parser("issue")
issue_command.add_argument("--ca-dir", type=Path, required=True)
issue_command.add_argument("--output-dir", type=Path, required=True)
issue_command.add_argument("--name", required=True)
issue_command.add_argument("--hostname", required=True)
issue_command.add_argument("--lifetime-days", type=int, default=365)

bundle_command = commands.add_parser("bundle")
bundle_command.add_argument("--output-dir", type=Path, required=True)
bundle_command.add_argument("--force", action="store_true")

arguments = parser.parse_args()
if arguments.command == "ensure-ca":
    created = ensure_ca(
        arguments.ca_dir,
        lifetime_days=arguments.lifetime_days,
        force=arguments.force,
    )
    print("CA created" if created else "CA is valid")
elif arguments.command == "issue":
    issue_certificate(
        arguments.ca_dir,
        arguments.output_dir,
        name=arguments.name,
        hostname=arguments.hostname,
        lifetime_days=arguments.lifetime_days,
    )
    print(f"Issued certificate: {arguments.output_dir / arguments.name}.crt")
else:
    generate_bundle(arguments.output_dir, force=arguments.force)
    print(f"Generated mTLS certificate bundle in {arguments.output_dir}")
