"""Configuration loading for vvm.

Configuration lives in ``$XDG_CONFIG_HOME/vvm/config.toml`` (default
``~/.config/vvm/config.toml``). Everything has a sensible default so the file
is entirely optional.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vvm.toml_io import read_toml

DEFAULT_VENV_NAMES: tuple[str, ...] = (".venv", "venv", "env", ".virtualenv", "virtualenv")
DEFAULT_PROJECT_FILES: tuple[str, ...] = ("pyproject.toml", "requirements.txt")


def _xdg_config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def _xdg_cache_home() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")


def _default_search_dirs() -> tuple[Path, ...]:
    candidates = []
    workon_home = os.environ.get("WORKON_HOME")
    if workon_home:
        candidates.append(Path(workon_home))
    candidates.append(Path.home() / ".virtualenvs")
    candidates.append(Path.home() / ".local" / "share" / "virtualenvs")
    return _expand_unique(candidates)


def _expand_unique(paths: Iterable[Path]) -> tuple[Path, ...]:
    unique = []
    for raw in paths:
        path = Path(raw).expanduser()
        if path not in unique:
            unique.append(path)
    return tuple(unique)


@dataclass(frozen=True)
class Config:
    """Resolved runtime configuration."""

    search_dirs: tuple[Path, ...] = field(default_factory=_default_search_dirs)
    cache_path: Path = field(default_factory=lambda: _xdg_cache_home() / "vvm" / "venvs.json")
    venv_names: tuple[str, ...] = DEFAULT_VENV_NAMES
    project_files: tuple[str, ...] = DEFAULT_PROJECT_FILES

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> Config:
        """Build a config from a parsed mapping, falling back to defaults."""
        search_dirs = data.get("search_dirs")
        cache_path = data.get("cache_path")
        return cls(
            search_dirs=(
                _expand_unique(Path(p) for p in search_dirs)
                if search_dirs is not None
                else _default_search_dirs()
            ),
            cache_path=(
                Path(cache_path).expanduser()
                if cache_path is not None
                else _xdg_cache_home() / "vvm" / "venvs.json"
            ),
            venv_names=tuple(data.get("venv_names", DEFAULT_VENV_NAMES)),
            project_files=tuple(data.get("project_files", DEFAULT_PROJECT_FILES)),
        )


class ConfigLoader:
    """Loads :class:`Config` from a TOML file, or defaults when absent."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path).expanduser() if path is not None else self.default_path()

    @staticmethod
    def default_path() -> Path:
        return _xdg_config_home() / "vvm" / "config.toml"

    def load(self) -> Config:
        data: dict[str, Any] = read_toml(self.path) if self.path.is_file() else {}
        return Config.from_mapping(data)
