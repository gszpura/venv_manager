"""Virtual environment classification.

Classification is an ordered, config-driven strategy: the first
:class:`~vvm.models.CategoryRule` with an installed "prolific" package wins.
An empty rule acts as the catch-all, and with no rules at all environments are
labelled ``unknown``.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from collections.abc import Sequence
from pathlib import Path

from vvm.models import UNKNOWN_CATEGORY, CategoryRule


class CategoryClassifier(ABC):
    @abstractmethod
    def classify(self, venv_path: Path, packages: frozenset) -> tuple[str, ...]:
        """Return the categories this environment belongs to."""

    @property
    def signature(self) -> str:
        """Stable identifier for the classification rules.

        Folded into the venv cache fingerprint so that changing the rules
        invalidates cached classifications.
        """
        return ""


class DefaultCategoryClassifier(CategoryClassifier):
    """Assigns the first matching rule, else ``unknown``."""

    def __init__(self, rules: Sequence[CategoryRule] = ()) -> None:
        self.rules = tuple(rules)

    @property
    def signature(self) -> str:
        payload = ";".join(
            f"{rule.name}={','.join(sorted(rule.packages))}" for rule in self.rules
        )
        return hashlib.sha1(payload.encode()).hexdigest()

    def classify(self, venv_path: Path, packages: frozenset) -> tuple[str, ...]:
        for rule in self.rules:
            if not rule.packages or packages & rule.packages:
                return (rule.name,)
        return (UNKNOWN_CATEGORY,)
