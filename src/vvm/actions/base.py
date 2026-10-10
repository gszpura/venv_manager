"""Base class for CLI-facing features."""

from __future__ import annotations

import sys
from abc import ABC, abstractmethod
from typing import TextIO


class Action(ABC):
    """Base class for a runnable user-facing operation.

    ``run`` performs the action and returns a process exit code (``0`` on
    success). Subclasses share a single output stream via ``self.out``.
    """

    def __init__(self, out: TextIO | None = None) -> None:
        self.out = out or sys.stdout

    @abstractmethod
    def run(self) -> int:
        """Perform the action and return a process exit code."""
