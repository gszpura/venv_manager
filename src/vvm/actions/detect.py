"""The ``detect`` action: list discovered virtual environments."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import TextIO

from vvm.detection import VenvDetector
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


class DetectAction:
    """Detects venvs and prints a one-line summary for each."""

    def __init__(
        self,
        detector: VenvDetector,
        formatter: VenvFormatter | None = None,
        out: TextIO | None = None,
    ) -> None:
        self.detector = detector
        self.formatter = formatter or PlainVenvFormatter()
        self.out = out or sys.stdout

    def run(self) -> int:
        venvs = self.detector.detect()
        if not venvs:
            print("No virtual environments found.", file=self.out)
            return 0
        for venv in venvs:
            print(self.formatter.format(venv), file=self.out)
        return 0
