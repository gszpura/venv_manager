"""The ``unlink`` action: remove the venv link created by ``best``."""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from vvm.actions.base import Action
from vvm.actions.best import DEFAULT_LINK_NAME
from vvm.config import Config
from vvm.linking import LinkingError, SymlinkLinker, VenvLinker


class UnlinkAction(Action):
    """Removes the project's venv symlink (e.g. ``.venv``) if it exists."""

    def __init__(
        self,
        linker: VenvLinker,
        project_dir: Path | None = None,
        link_name: str = DEFAULT_LINK_NAME,
        out: TextIO | None = None,
    ) -> None:
        super().__init__(out)
        self.linker = linker
        self.project_dir = Path(project_dir) if project_dir is not None else Path.cwd()
        self.link_name = link_name

    @classmethod
    def build(
        cls,
        config: Config,
        *,
        project_dir: Path | None = None,
        link_name: str = DEFAULT_LINK_NAME,
        out: TextIO | None = None,
    ) -> UnlinkAction:
        """Build an unlink action for ``project_dir`` (default: cwd)."""
        return cls(linker=SymlinkLinker(), project_dir=project_dir, link_name=link_name, out=out)

    def run(self) -> int:
        target = self.project_dir / self.link_name
        try:
            removed = self.linker.unlink(target)
        except LinkingError as exc:
            print(str(exc), file=self.out)
            return 1
        if removed is None:
            print(f"No link found at {target}.", file=self.out)
            return 1
        print(f"Removed {removed}", file=self.out)
        return 0
