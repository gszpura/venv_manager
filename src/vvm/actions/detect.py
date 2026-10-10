"""The ``detect`` action: list discovered virtual environments."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TextIO

from vvm.actions.base import Action
from vvm.config import Config
from vvm.detection import VenvDetector, build_detector
from vvm.models import Venv


class VenvFormatter(ABC):
    """Renders a single venv as one summary line."""

    @abstractmethod
    def format(self, venv: Venv) -> str:
        """Return the display line for ``venv``."""


class PlainVenvFormatter(VenvFormatter):
    """``<path> [<category>] <n> packages``"""

    def format(self, venv: Venv) -> str:
        return f"{venv.path} [{venv.primary_category.value}] {venv.package_count} packages"


class DetectAction(Action):
    """Detects venvs and prints a one-line summary for each."""

    def __init__(
        self,
        detector: VenvDetector,
        formatter: VenvFormatter | None = None,
        out: TextIO | None = None,
    ) -> None:
        super().__init__(out)
        self.detector = detector
        self.formatter = formatter or PlainVenvFormatter()

    @classmethod
    def build(
        cls,
        config: Config,
        *,
        directory: Path | None = None,
        use_cache: bool = True,
        out: TextIO | None = None,
    ) -> DetectAction:
        """Build a detect action wired with its own detector for ``directory``."""
        target = Path(directory) if directory is not None else Path.cwd()
        detector = build_detector(config, target, use_cache=use_cache)
        return cls(detector, out=out)

    def run(self) -> int:
        venvs = self.detector.detect()
        if not venvs:
            print("No virtual environments found.", file=self.out)
            return 0
        for venv in venvs:
            print(self.formatter.format(venv), file=self.out)
        return 0
