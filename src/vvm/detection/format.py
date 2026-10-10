"""Display formatting for detected virtual environments.

Formatters live here (not in the actions) so any command can render venvs the
same way. Tables are drawn with ``tabulate`` using Unicode box-drawing lines,
and colors are plain ANSI sequences enabled only for interactive terminals.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TextIO

from tabulate import tabulate

from vvm.models import Venv

_RESET = "\x1b[0m"
_BOLD = "\x1b[1m"

_CATEGORY_COLORS = {
    "ai": "\x1b[35m",  # magenta
    "data_science": "\x1b[36m",  # cyan
    "server": "\x1b[32m",  # green
    "other": "\x1b[33m",  # yellow
    "unknown": "\x1b[90m",  # bright black / grey
}
_DEFAULT_COLOR = "\x1b[37m"  # white


def supports_color(stream: TextIO) -> bool:
    """Whether ANSI colors should be written to ``stream``."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return bool(getattr(stream, "isatty", lambda: False)())


def colorize(text: str, code: str, enabled: bool) -> str:
    """Wrap ``text`` in the ANSI ``code`` when ``enabled``."""
    return f"{code}{text}{_RESET}" if enabled else text


def category_color(category: str) -> str:
    """Return the ANSI color code for ``category``."""
    return _CATEGORY_COLORS.get(category, _DEFAULT_COLOR)


class VenvFormatter(ABC):
    """Renders a collection of virtual environments for display."""

    @abstractmethod
    def render(self, venvs: Sequence[Venv]) -> str:
        """Return the display text for ``venvs``."""


class TextVenvFormatter(VenvFormatter):
    """One ``<path> [<category>] <n> packages`` line per venv."""

    def render(self, venvs: Sequence[Venv]) -> str:
        return "\n".join(
            f"{venv.path} [{venv.primary_category}] {venv.package_count} packages"
            for venv in venvs
        )


class TableVenvFormatter(VenvFormatter):
    """A solid-bordered table with Path, Category and Packages columns."""

    HEADERS = ("Path", "Category", "Packages")

    def __init__(self, color: bool = False) -> None:
        self.color = color

    def render(self, venvs: Sequence[Venv]) -> str:
        rows = [
            (
                str(venv.path),
                colorize(venv.primary_category, category_color(venv.primary_category), self.color),
                str(venv.package_count),
            )
            for venv in venvs
        ]
        headers = tuple(colorize(header, _BOLD, self.color) for header in self.HEADERS)
        return tabulate(rows, headers=headers, tablefmt="rounded_outline")
