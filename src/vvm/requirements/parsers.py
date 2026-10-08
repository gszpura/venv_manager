"""Parse project dependencies from ``pyproject.toml`` or ``requirements.txt``."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from vvm.models import Requirement
from vvm.toml_io import read_toml

_NAME_RE = re.compile(r"\s*([A-Za-z0-9][A-Za-z0-9._-]*)")
_EXTRAS_RE = re.compile(r"\s*\[([^\]]*)\]")
_INCLUDE_RE = re.compile(r"^\s*(?:-r|--requirement)\s+(?P<path>\S+)")


def parse_requirement(text: str) -> Requirement | None:
    """Parse a PEP 508 / requirements.txt style requirement string.

    Only the distribution name is required for matching; extras and the
    specifier are captured opportunistically.
    """
    raw = text.strip()
    if not raw or raw.startswith("#"):
        return None
    match = _NAME_RE.match(raw)
    if not match:
        return None
    name = match.group(1)
    rest = raw[match.end():]
    extras: frozenset = frozenset()
    extras_match = _EXTRAS_RE.match(rest)
    if extras_match:
        extras = frozenset(
            extra.strip() for extra in extras_match.group(1).split(",") if extra.strip()
        )
        rest = rest[extras_match.end():]
    specifier = rest.split(";", 1)[0].strip() or None
    if specifier and specifier.startswith("@"):
        specifier = None
    return Requirement(name=name, raw=raw, specifier=specifier, extras=extras)


def _dedupe(requirements: Iterable[Requirement]) -> list[Requirement]:
    seen = set()
    unique = []
    for requirement in requirements:
        if requirement.name in seen:
            continue
        seen.add(requirement.name)
        unique.append(requirement)
    return unique


@dataclass
class ProjectRequirements:
    """Requirements discovered for a project, with their source file."""

    source: Path
    requirements: list[Requirement] = field(default_factory=list)

    @property
    def names(self) -> frozenset:
        return frozenset(requirement.name for requirement in self.requirements)


class RequirementsParser(ABC):
    @abstractmethod
    def parse(self, path: Path) -> list[Requirement]:
        """Return the requirements declared in ``path``."""


class RequirementsTxtParser(RequirementsParser):
    """Parses ``requirements.txt`` including ``-r`` includes."""

    def parse(self, path: Path) -> list[Requirement]:
        return _dedupe(self._parse(Path(path), seen=set()))

    def _parse(self, path: Path, seen: set) -> list[Requirement]:
        resolved = path.resolve()
        if resolved in seen or not path.is_file():
            return []
        seen.add(resolved)

        requirements: list[Requirement] = []
        for line in path.read_text().splitlines():
            include = _INCLUDE_RE.match(line)
            if include:
                requirements.extend(self._parse(path.parent / include.group("path"), seen))
                continue
            if line.lstrip().startswith("-"):
                continue
            line = line.split(" #", 1)[0]
            requirement = parse_requirement(line)
            if requirement is not None:
                requirements.append(requirement)
        return requirements


class PyprojectParser(RequirementsParser):
    """Parses ``[project].dependencies`` (PEP 621), falling back to Poetry."""

    def parse(self, path: Path) -> list[Requirement]:
        data = read_toml(Path(path))
        dependency_strings = list(data.get("project", {}).get("dependencies", []))
        if not dependency_strings:
            poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            dependency_strings = [name for name in poetry if name.lower() != "python"]
        return _dedupe(
            requirement
            for requirement in (parse_requirement(item) for item in dependency_strings)
            if requirement is not None
        )


class ProjectRequirementsReader:
    """Selects the right project file and delegates parsing.

    Files are tried in the configured order; the first one present wins.
    """

    def __init__(
        self,
        parsers: Mapping[str, RequirementsParser],
        filenames: Sequence[str],
        default_parser: RequirementsParser,
    ) -> None:
        self.parsers = dict(parsers)
        self.filenames = tuple(filenames)
        self.default_parser = default_parser

    def read(self, project_dir: Path) -> ProjectRequirements | None:
        project_dir = Path(project_dir)
        for filename in self.filenames:
            path = project_dir / filename
            if not path.is_file():
                continue
            parser = self.parsers.get(filename, self.default_parser)
            return ProjectRequirements(source=path, requirements=parser.parse(path))
        return None


def default_reader(project_files: Sequence[str]) -> ProjectRequirementsReader:
    """Build a reader with the built-in parsers."""
    parsers: dict[str, RequirementsParser] = {
        "requirements.txt": RequirementsTxtParser(),
        "pyproject.toml": PyprojectParser(),
    }
    return ProjectRequirementsReader(parsers, project_files, default_parser=PyprojectParser())
