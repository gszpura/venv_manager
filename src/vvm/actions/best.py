"""The ``best`` action: pick and link the best venv for a project."""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from vvm.actions.base import Action
from vvm.detection import VenvDetector
from vvm.linking import VenvLinker
from vvm.matching import VenvMatcher
from vvm.requirements import ProjectRequirementsReader

DEFAULT_LINK_NAME = ".venv"


class BestAction(Action):
    """Reads project requirements, chooses the best venv and links it.

    A complete match is linked (unless linking is disabled) and the action
    returns ``0``. When no venv covers the requirements, the closest match and
    its missing packages are reported and the action returns ``1``.
    """

    def __init__(
        self,
        detector: VenvDetector,
        reader: ProjectRequirementsReader,
        matcher: VenvMatcher,
        linker: VenvLinker | None = None,
        project_dir: Path | None = None,
        link: bool = True,
        force: bool = False,
        link_name: str = DEFAULT_LINK_NAME,
        out: TextIO | None = None,
    ) -> None:
        super().__init__(out)
        self.detector = detector
        self.reader = reader
        self.matcher = matcher
        self.linker = linker
        self.project_dir = Path(project_dir) if project_dir is not None else Path.cwd()
        self.link = link
        self.force = force
        self.link_name = link_name

    def run(self) -> int:
        requirements = self.reader.read(self.project_dir)
        if requirements is None:
            print(f"No project requirements found in {self.project_dir}.", file=self.out)
            return 1

        venvs = self.detector.detect()
        if not venvs:
            print("No virtual environments found.", file=self.out)
            return 1

        best = self.matcher.best(requirements.requirements, venvs)
        if best is None:  # pragma: no cover - venvs is non-empty
            return 1

        print(
            f"Best match: {best.venv.path} "
            f"({best.extra_count} extra packages)",
            file=self.out,
        )
        if not best.is_complete:
            print(
                f"Not all requirements are covered; missing {len(best.missing)}: "
                f"{', '.join(sorted(best.missing))}",
                file=self.out,
            )
            return 1

        if self.link and self.linker is not None:
            target = self.project_dir / self.link_name
            linked = self.linker.link(best.venv, target, force=self.force)
            print(f"Linked {linked} -> {best.venv.path}", file=self.out)
        return 0
