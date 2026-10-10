"""Configuration loading for vvm.

Configuration lives in ``$XDG_CONFIG_HOME/vvm/config.toml`` (default
``~/.config/vvm/config.toml``). Everything has a sensible default so the file
is entirely optional.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from vvm.category_defaults import DEFAULT_CONFIG_TOML
from vvm.models import CategoryRule, normalize_name
from vvm.toml_io import read_toml

DEFAULT_VENV_NAMES: tuple[str, ...] = (".venv", "venv", "env", ".virtualenv", "virtualenv")
DEFAULT_PROJECT_FILES: tuple[str, ...] = ("pyproject.toml", "requirements.txt")
DEFAULT_SEARCH_DEPTH = 3


def _xdg_config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config")


def _xdg_cache_home() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / ".cache")


def _xdg_data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local" / "share")


def _user_cache_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Caches"
    return _xdg_cache_home()


def _user_data_dir() -> Path:
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support"
    return _xdg_data_home()


def _env_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value).expanduser() if value else None


def _split_paths(value: str | None) -> list[Path]:
    if not value:
        return []
    return [Path(part).expanduser() for part in value.split(os.pathsep) if part]


def _default_search_dirs() -> tuple[Path, ...]:
    """Centralized virtualenv stores used by common Python tooling.

    Missing directories are harmless: the locator skips anything that does not
    exist, so it is safe to list every well-known default.
    """
    home = Path.home()
    data_dir = _user_data_dir()
    cache_dir = _user_cache_dir()
    candidates: list[Path] = []

    # virtualenvwrapper / virtualfish / pew
    workon_home = _env_path("WORKON_HOME")
    if workon_home is not None:
        candidates.append(workon_home)
    candidates.append(home / ".virtualenvs")

    # pipenv / pew share the XDG data location
    candidates.append(home / ".local" / "share" / "virtualenvs")

    # poetry
    poetry_path = _env_path("POETRY_VIRTUALENVS_PATH")
    if poetry_path is not None:
        candidates.append(poetry_path)
    else:
        poetry_cache = _env_path("POETRY_CACHE_DIR") or cache_dir
        candidates.append(poetry_cache / "pypoetry" / "virtualenvs")

    # pdm
    candidates.append(data_dir / "pdm" / "venvs")

    # pipx
    candidates.append((_env_path("PIPX_HOME") or data_dir / "pipx") / "venvs")

    # pyenv-virtualenv (flat <name> entries; nested <py>/envs handled by depth)
    candidates.append((_env_path("PYENV_ROOT") or home / ".pyenv") / "versions")

    # conda
    candidates.extend(_split_paths(os.environ.get("CONDA_ENVS_PATH")))
    candidates.extend(
        [
            home / ".conda" / "envs",
            home / "miniconda3" / "envs",
            home / "anaconda3" / "envs",
            home / "miniforge3" / "envs",
            home / "opt" / "anaconda3" / "envs",
            home / "opt" / "miniconda3" / "envs",
            Path("/opt/conda/envs"),
        ]
    )

    # micromamba / mamba
    candidates.append((_env_path("MAMBA_ROOT_PREFIX") or home) / "micromamba" / "envs")
    candidates.append(data_dir / "mamba" / "envs")

    # hatch (nested: <project>/<env>/<hash>)
    candidates.append(data_dir / "hatch" / "env" / "virtual")

    return _expand_unique(candidates)


def _expand_unique(paths: Iterable[Path]) -> tuple[Path, ...]:
    unique = []
    for raw in paths:
        path = Path(raw).expanduser()
        if path not in unique:
            unique.append(path)
    return tuple(unique)


def _parse_categories(value: Any) -> tuple[CategoryRule, ...]:
    """Build ordered category rules from the ``[categories]`` config table.

    The table's key order is the priority order. Anything malformed is skipped
    so a broken entry never breaks classification.
    """
    if not isinstance(value, Mapping):
        return ()
    rules = []
    for name, packages in value.items():
        if not isinstance(name, str) or not name.strip() or not _is_sequence(packages):
            continue
        normalized = frozenset(
            normalize_name(package) for package in packages if isinstance(package, str) and package.strip()
        )
        rules.append(CategoryRule(name=name.strip(), packages=normalized))
    return tuple(rules)


def _is_sequence(value: Any) -> bool:
    return isinstance(value, Iterable) and not isinstance(value, (str, bytes))


@dataclass(frozen=True)
class Config:
    """Resolved runtime configuration."""

    search_dirs: tuple[Path, ...] = field(default_factory=_default_search_dirs)
    cache_path: Path = field(default_factory=lambda: _xdg_cache_home() / "vvm" / "venvs.json")
    venv_names: tuple[str, ...] = DEFAULT_VENV_NAMES
    project_files: tuple[str, ...] = DEFAULT_PROJECT_FILES
    search_depth: int = DEFAULT_SEARCH_DEPTH
    categories: tuple[CategoryRule, ...] = ()

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
            search_depth=max(1, int(data.get("search_depth", DEFAULT_SEARCH_DEPTH))),
            categories=_parse_categories(data.get("categories")),
        )


class ConfigLoader:
    """Loads :class:`Config` from a TOML file, or defaults when absent."""

    def __init__(self, path: Path | None = None) -> None:
        self.path = Path(path).expanduser() if path is not None else self.default_path()

    @staticmethod
    def default_path() -> Path:
        return _xdg_config_home() / "vvm" / "config.toml"

    def load(self) -> Config:
        if not self.path.is_file():
            self._create_default()
        data: dict[str, Any] = read_toml(self.path) if self.path.is_file() else {}
        return Config.from_mapping(data)

    def _create_default(self) -> None:
        """Seed a new config file (with default categories) on first run."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.path.write_text(DEFAULT_CONFIG_TOML)
        except OSError:
            pass
