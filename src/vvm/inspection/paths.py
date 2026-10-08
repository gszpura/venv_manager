"""Low-level helpers for locating the parts of a virtual environment.

These are shared by detection (validating a candidate) and inspection
(executing the interpreter / reading metadata), so the platform-specific path
logic lives in exactly one place.
"""

from __future__ import annotations

from pathlib import Path

_PYTHON_NAMES = ("python", "python3", "python.exe")


def pyvenv_cfg(venv_path: Path) -> Path | None:
    candidate = Path(venv_path) / "pyvenv.cfg"
    return candidate if candidate.is_file() else None


def find_python(venv_path: Path) -> Path | None:
    venv_path = Path(venv_path)
    for folder in ("bin", "Scripts"):
        for name in _PYTHON_NAMES:
            candidate = venv_path / folder / name
            if candidate.exists():
                return candidate
    return None


def find_site_packages(venv_path: Path) -> Path | None:
    venv_path = Path(venv_path)
    for pattern in ("lib/python*/site-packages", "Lib/site-packages"):
        for candidate in sorted(venv_path.glob(pattern)):
            if candidate.is_dir():
                return candidate
    return None


def read_pyvenv_cfg(venv_path: Path) -> dict[str, str]:
    path = pyvenv_cfg(venv_path)
    if path is None:
        return {}
    config: dict[str, str] = {}
    for line in path.read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep:
            config[key.strip()] = value.strip()
    return config


def is_venv(venv_path: Path) -> bool:
    if pyvenv_cfg(venv_path) is not None:
        return True
    return find_python(venv_path) is not None and find_site_packages(venv_path) is not None
