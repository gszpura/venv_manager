"""Small TOML reading helper shared by config and requirements parsing."""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any


def read_toml(path: Path) -> dict[str, Any]:
    """Read and parse a TOML file."""
    with Path(path).open("rb") as handle:
        return tomllib.load(handle)
