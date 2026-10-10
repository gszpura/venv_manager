#!/usr/bin/env python3
"""Build a single-file ``vvm.pyz`` executable.

The package and its runtime dependencies are bundled into one runnable zip
archive (a zipapp) with a ``#!/usr/bin/env python3`` shebang, so the result
only needs a Python 3.11+ interpreter:

    ./dist/vvm.pyz detect

Dependencies declared in ``pyproject.toml`` are copied from the current
environment when available; anything missing is installed into a temporary
location via ``uv``/``pip`` before being bundled.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
import zipapp
from importlib import metadata
from pathlib import Path

_MAIN = "from vvm.cli import main\n\nraise SystemExit(main())\n"
_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")
_NAME_RE = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)")


def _dependencies(root: Path) -> list[str]:
    data = tomllib.loads((root / "pyproject.toml").read_text())
    return list(data.get("project", {}).get("dependencies", []))


def _requirement_name(requirement: str) -> str:
    match = _NAME_RE.match(requirement)
    if not match:
        raise ValueError(f"cannot parse requirement: {requirement!r}")
    return match.group(1)


def _copy_distribution(name: str, target: Path) -> None:
    dist = metadata.distribution(name)
    for file in dist.files or ():
        if file.suffix == ".pyc" or ".." in file.parts:
            continue
        source = dist.locate_file(file)
        if not source.is_file():
            continue
        destination = target / file
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def _install(requirements: list[str], target: Path) -> None:
    attempts = (
        [sys.executable, "-m", "pip", "install", "--quiet", "--target", str(target), *requirements],
        ["uv", "pip", "install", "--quiet", "--python", sys.executable, "--target", str(target), *requirements],
    )
    for command in attempts:
        try:
            subprocess.run(command, check=True)
            return
        except (OSError, subprocess.CalledProcessError):
            continue
    raise RuntimeError(
        "could not bundle dependencies; install them first (e.g. `pip install .`) "
        f"or make sure `pip`/`uv` is available: {', '.join(requirements)}"
    )


def _bundle_dependencies(requirements: list[str], target: Path) -> None:
    missing = []
    for requirement in requirements:
        try:
            _copy_distribution(_requirement_name(requirement), target)
        except metadata.PackageNotFoundError:
            missing.append(requirement)
    if missing:
        _install(missing, target)


def build(output: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    package = root / "src" / "vvm"
    if not package.is_dir():
        raise FileNotFoundError(f"package not found: {package}")

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp)
        shutil.copytree(package, staging / "vvm", ignore=_IGNORE)
        _bundle_dependencies(_dependencies(root), staging)
        (staging / "__main__.py").write_text(_MAIN)
        output.parent.mkdir(parents=True, exist_ok=True)
        zipapp.create_archive(staging, target=output, interpreter="/usr/bin/env python3")
    output.chmod(0o755)
    return output


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a standalone vvm.pyz")
    parser.add_argument(
        "-o",
        "--output",
        default="dist/vvm.pyz",
        help="output path (default: dist/vvm.pyz)",
    )
    args = parser.parse_args()
    path = build(Path(args.output))
    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
