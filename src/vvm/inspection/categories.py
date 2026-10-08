"""Virtual environment classification.

Classification is intentionally a pluggable strategy: the default returns
``UNKNOWN`` today, and future rules (data-science, web, tooling...) can be
added without touching detection.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from vvm.models import VenvCategory


class CategoryClassifier(ABC):
    @abstractmethod
    def classify(self, venv_path: Path, packages: frozenset) -> tuple[VenvCategory, ...]:
        """Return the categories this environment belongs to."""


class DefaultCategoryClassifier(CategoryClassifier):
    """Placeholder classifier that labels every environment ``UNKNOWN``."""

    def classify(self, venv_path: Path, packages: frozenset) -> tuple[VenvCategory, ...]:
        return (VenvCategory.UNKNOWN,)
