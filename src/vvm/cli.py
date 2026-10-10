"""Command-line interface for vvm."""

from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from vvm import __version__
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

    list_cmd = subparsers.add_parser("list", help="alias for detect")
    _add_common_options(list_cmd)

    config = subparsers.add_parser(
        "config", help="show the config file path, its contents and default search paths"
    )
    _add_common_options(config)

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

    unlink = subparsers.add_parser("unlink", help="remove the venv link from a project")
    _add_common_options(unlink)
    unlink.add_argument(
        "--link-name",
        default=".venv",
        help="name of the link to remove in the project (default: .venv)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path = getattr(args, "config", None)
    use_cache = not getattr(args, "no_cache", False)
    manager = VenvManager(config_path=Path(config_path) if config_path else None)

    directory = Path(getattr(args, "directory", "."))
    if args.command in ("detect", "list"):
        return manager.run("detect", directory=directory, use_cache=use_cache)
    if args.command == "config":
        return manager.run("config", config_path=manager.config_path)
    if args.command == "best":
        return manager.run(
            "best",
            project_dir=directory,
            link=args.link,
            force=args.force,
            link_name=args.link_name,
            use_cache=use_cache,
        )
    if args.command == "unlink":
        return manager.run("unlink", project_dir=directory, link_name=args.link_name)
    parser.error(f"unknown command: {args.command}")  # pragma: no cover
    return 2
