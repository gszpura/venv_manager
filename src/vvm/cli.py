"""Command-line interface for vvm."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from vvm import __version__
from vvm.config import ConfigLoader
from vvm.manager import VenvManager


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "-C",
        "--directory",
        default=argparse.SUPPRESS,
        help="directory to search / project directory (default: current directory)",
    )
    parser.add_argument(
        "--config",
        default=argparse.SUPPRESS,
        help="path to a config TOML file",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        default=argparse.SUPPRESS,
        help="ignore and do not write the venv cache",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="vvm",
        description="Discover and match Python virtual environments.",
    )
    parser.add_argument("--version", action="version", version=f"vvm {__version__}")
    _add_common_options(parser)

    subparsers = parser.add_subparsers(dest="command", required=True)

    detect = subparsers.add_parser("detect", help="list detected virtual environments")
    _add_common_options(detect)

    best = subparsers.add_parser("best", help="find and link the best venv for a project")
    _add_common_options(best)
    best.add_argument(
        "--link",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="symlink the best venv into the project (default: enabled)",
    )
    best.add_argument(
        "--force",
        action="store_true",
        help="replace an existing link or empty directory",
    )
    best.add_argument(
        "--link-name",
        default=".venv",
        help="name of the link to create in the project (default: .venv)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path = getattr(args, "config", None)
    config = ConfigLoader(Path(config_path)).load() if config_path else ConfigLoader().load()
    manager = VenvManager(config=config, use_cache=not getattr(args, "no_cache", False))

    directory = Path(getattr(args, "directory", "."))
    if args.command == "detect":
        return manager.detect(directory=directory)
    if args.command == "best":
        return manager.best(
            project_dir=directory,
            link=args.link,
            force=args.force,
            link_name=args.link_name,
        )
    parser.error(f"unknown command: {args.command}")  # pragma: no cover
    return 2
