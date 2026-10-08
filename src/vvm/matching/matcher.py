"""Matching project requirements against detected virtual environments."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Sequence

from vvm.models import MatchResult, Requirement, Venv


class RequirementComparator(ABC):
    """Decides whether an installed package set satisfies a requirement."""

    @abstractmethod
    def satisfied_by(self, requirement: Requirement, packages: frozenset) -> bool:
        """Return ``True`` if ``packages`` satisfies ``requirement``."""


class NameComparator(RequirementComparator):
    """Name-only comparison; versions are ignored for now."""

    def satisfied_by(self, requirement: Requirement, packages: frozenset) -> bool:
        return requirement.name in packages


class ScoringStrategy(ABC):
    """Ranks match results; a lower score is a better match."""

    @abstractmethod
    def score(self, missing: frozenset, extra: frozenset, venv: Venv) -> tuple:
        """Return a comparable tuple for a single match."""


class MinimalCoverageScoring(ScoringStrategy):
    """Prefer complete matches with the fewest extras.

    Primary key is the number of missing packages (so a complete venv always
    beats an incomplete one), secondary key is the number of extra packages
    (so the leanest covering venv wins). For incomplete matches this naturally
    surfaces the closest venv and its missing packages.
    """

    def score(self, missing: frozenset, extra: frozenset, venv: Venv) -> tuple:
        return (len(missing), len(extra), venv.package_count)


class VenvMatcher:
    """Scores each detected venv against a set of requirements."""

    def __init__(
        self,
        comparator: RequirementComparator | None = None,
        scoring: ScoringStrategy | None = None,
    ) -> None:
        self.comparator = comparator or NameComparator()
        self.scoring = scoring or MinimalCoverageScoring()

    def match(self, requirements: Iterable[Requirement], venvs: Iterable[Venv]) -> list[MatchResult]:
        """Return results for every venv, best match first."""
        reqs = requirement_list(requirements)
        required_names = {requirement.name for requirement in reqs}
        results = [self._match_one(required_names, reqs, venv) for venv in venvs]
        return sorted(results, key=lambda result: result.score)

    def best(self, requirements: Iterable[Requirement], venvs: Iterable[Venv]) -> MatchResult | None:
        """Return the single best match, or ``None`` when there are no venvs."""
        results = self.match(requirements, venvs)
        return results[0] if results else None

    def _match_one(self, required_names: set, requirements: Sequence[Requirement], venv: Venv) -> MatchResult:
        missing = frozenset(
            requirement.name
            for requirement in requirements
            if not self.comparator.satisfied_by(requirement, venv.packages)
        )
        extra = frozenset(venv.packages - required_names)
        return MatchResult(
            venv=venv,
            missing=missing,
            extra=extra,
            score=self.scoring.score(missing, extra, venv),
        )


def requirement_list(requirements: Iterable[Requirement]) -> list[Requirement]:
    """Materialize and dedupe requirements by normalized name."""
    seen = set()
    unique = []
    for requirement in requirements:
        if requirement.name in seen:
            continue
        seen.add(requirement.name)
        unique.append(requirement)
    return unique
