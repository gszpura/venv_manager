"""Core domain models shared across vvm.

These are intentionally free of I/O so every layer (detection, inspection,
requirements, matching, actions) can depend on them without pulling in the
rest of the tool.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

_NORMALIZE_RE = re.compile(r"[-_.]+")


def normalize_name(name: str) -> str:
    """Normalize a distribution name following PEP 503."""
    return _NORMALIZE_RE.sub("-", name).strip().lower()


class VenvCategory(str, Enum):
    """Category assigned to a virtual environment.

    Only ``UNKNOWN`` exists for now; the enum is the single extension point
    for future classification rules.
    """

    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Requirement:
    """A single project dependency.

    ``name`` is always PEP 503 normalized. ``specifier`` and ``extras`` are
    captured for future use but ignored by name-only matching.
    """

    name: str
    raw: str = ""
    specifier: str | None = None
    extras: frozenset = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", normalize_name(self.name))


@dataclass(frozen=True)
class Venv:
    """A discovered virtual environment and its installed packages."""

    path: Path
    packages: frozenset = field(default_factory=frozenset)
    python_version: str | None = None
    categories: tuple[VenvCategory, ...] = ()

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def package_count(self) -> int:
        return len(self.packages)

    @property
    def primary_category(self) -> VenvCategory:
        return self.categories[0] if self.categories else VenvCategory.UNKNOWN


@dataclass(frozen=True)
class MatchResult:
    """Outcome of matching one :class:`Venv` against project requirements.

    ``missing`` holds required package names absent from the venv; ``extra``
    holds installed packages not requested. ``score`` is a comparable tuple
    produced by the scoring strategy (lower is better).
    """

    venv: Venv
    missing: frozenset = field(default_factory=frozenset)
    extra: frozenset = field(default_factory=frozenset)
    score: tuple = ()

    @property
    def is_complete(self) -> bool:
        return not self.missing

    @property
    def extra_count(self) -> int:
        return len(self.extra)
