"""The ``config`` action: show the config file and built-in defaults."""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import TextIO

from vvm.actions.base import Action

_SEPARATOR = "-" * 31


class ConfigAction(Action):
    """Prints the config path, its contents and the default search paths."""

    def __init__(
        self,
        config_path: Path,
        default_search_dirs: Iterable[Path],
        out: TextIO | None = None,
    ) -> None:
        super().__init__(out)
        self.config_path = Path(config_path)
        self.default_search_dirs = tuple(Path(p) for p in default_search_dirs)

    def run(self) -> int:
        content = self.config_path.read_text() if self.config_path.is_file() else ""

        print(f"Config path: {self.config_path}", file=self.out)
        print(_SEPARATOR, file=self.out)
        print("Config content:", file=self.out)
        print(content.rstrip("\n"), file=self.out)
        print(_SEPARATOR, file=self.out)
        print("Default search paths:", file=self.out)
        for path in self.default_search_dirs:
            print(path, file=self.out)
        return 0
