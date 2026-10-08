"""Linking a chosen virtual environment into a project directory."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from vvm.models import Venv


class LinkingError(Exception):
    """Raised when a link cannot be created safely."""


class VenvLinker(ABC):
    """Creates a link from a project path to a resolved virtual environment."""

    @abstractmethod
    def link(self, venv: Venv, target: Path, force: bool = False) -> Path:
        """Link ``target`` to ``venv`` and return the link path."""


class SymlinkLinker(VenvLinker):
    """Creates a symbolic link at ``target`` pointing at the venv.

    Existing links to the same venv are left untouched. Other existing entries
    require ``force``; non-empty directories are never removed automatically.
    """

    def link(self, venv: Venv, target: Path, force: bool = False) -> Path:
        source = Path(venv.path).resolve()
        target = Path(target)

        if target.is_symlink():
            if target.resolve() == source:
                return target
            if not force:
                raise LinkingError(f"{target} already exists (use --force to replace)")
            target.unlink()
        elif target.is_dir():
            if not force:
                raise LinkingError(f"{target} is an existing directory (use --force)")
            if any(target.iterdir()):
                raise LinkingError(f"refusing to remove non-empty directory {target}")
            target.rmdir()
        elif target.exists():
            if not force:
                raise LinkingError(f"{target} already exists (use --force to replace)")
            target.unlink()

        target.parent.mkdir(parents=True, exist_ok=True)
        target.symlink_to(source)
        return target
