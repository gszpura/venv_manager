#!/usr/bin/env python3
"""Build a single-file ``vvm.pyz`` executable.

vvm has no runtime dependencies, so the whole tool packages into one runnable
zip archive (a zipapp) with a ``#!/usr/bin/env python3`` shebang. Drop the
result on ``PATH`` and it behaves like any other command:

    ./dist/vvm.pyz detect
"""

from __future__ import annotations

import argparse
import shutil
import tempfile
import zipapp
from pathlib import Path

_MAIN = "from vvm.cli import main\n\nraise SystemExit(main())\n"
_IGNORE = shutil.ignore_patterns("__pycache__", "*.pyc")


def build(output: Path) -> Path:
    root = Path(__file__).resolve().parents[1]
    package = root / "src" / "vvm"
    if not package.is_dir():
        raise FileNotFoundError(f"package not found: {package}")

    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp)
        shutil.copytree(package, staging / "vvm", ignore=_IGNORE)
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
