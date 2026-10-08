"""Action contract for CLI-facing features."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Action(Protocol):
    """A runnable user-facing operation.

    ``run`` performs the action and returns a process exit code (``0`` on
    success).
    """

    def run(self) -> int:
        ...
