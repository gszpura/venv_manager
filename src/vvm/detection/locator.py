"""Candidate location strategies for finding virtual environments."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence
from pathlib import Path

from vvm.inspection import is_venv


class LocationStrategy(ABC):
    """Yields candidate directories that may be virtual environments."""

    @abstractmethod
    def locate(self) -> Iterable[Path]:
        """Return candidate venv root paths (not necessarily valid)."""


class CurrentDirStrategy(LocationStrategy):
    """Looks for conventional venv folder names inside a project directory."""

    def __init__(self, directory: Path, venv_names: Sequence[str]) -> None:
        self.directory = Path(directory)
        self.venv_names = tuple(venv_names)

    def locate(self) -> Iterable[Path]:
        for name in self.venv_names:
            yield self.directory / name


class ConfiguredDirStrategy(LocationStrategy):
    """Scans the immediate children of each configured search directory."""

    def __init__(self, search_dirs: Iterable[Path]) -> None:
        self.search_dirs = tuple(Path(d) for d in search_dirs)

    def locate(self) -> Iterable[Path]:
        for search_dir in self.search_dirs:
            if not search_dir.is_dir():
                continue
            yield from sorted(search_dir.iterdir())


class VenvLocator:
    """Collects candidates from several strategies, deduplicating and keeping
    only entries that actually validate as virtual environments.

    Accepting already-resolved paths back is useful for tests and for callers
    that want to inspect a single known venv.
    """

    def __init__(self, strategies: Iterable[LocationStrategy] = ()) -> None:
        self.strategies = tuple(strategies)

    def locate(self) -> list[Path]:
        found: list[Path] = []
        seen = set()
        for candidate in self._candidates():
            try:
                key = candidate.resolve()
            except OSError:
                key = candidate
            if key in seen:
                continue
            seen.add(key)
            if is_venv(candidate):
                found.append(candidate)
        return found

    def _candidates(self) -> Iterable[Path]:
        for strategy in self.strategies:
            yield from strategy.locate()
