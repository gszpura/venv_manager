"""The ``detect`` action: list discovered virtual environments."""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from vvm.actions.base import Action
from vvm.config import Config
from vvm.detection import (
    TableVenvFormatter,
    TextVenvFormatter,
    VenvDetector,
    VenvFormatter,
    build_detector,
    supports_color,
)


class DetectAction(Action):
    """Detects venvs and prints them, as a table on a terminal."""

    def __init__(
        self,
        detector: VenvDetector,
        formatter: VenvFormatter | None = None,
        out: TextIO | None = None,
    ) -> None:
        super().__init__(out)
        self.detector = detector
        if formatter is not None:
            self.formatter = formatter
        elif supports_color(self.out):
            self.formatter = TableVenvFormatter(color=True)
        else:
            self.formatter = TextVenvFormatter()

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
        print(self.formatter.render(venvs), file=self.out)
        return 0
