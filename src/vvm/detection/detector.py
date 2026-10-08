"""Builds fully-resolved :class:`Venv` objects from located candidates."""

from __future__ import annotations

import re
from pathlib import Path

from vvm.cache import VenvCache, stat_fingerprint
from vvm.detection.locator import VenvLocator
from vvm.inspection import (
    CategoryClassifier,
    PackageInspector,
    find_site_packages,
    pyvenv_cfg,
    read_pyvenv_cfg,
)
from vvm.models import Venv

_VERSION_RE = re.compile(r"(\d+\.\d+(?:\.\d+)?)")


def python_version(venv_path: Path) -> str | None:
    config = read_pyvenv_cfg(venv_path)
    raw = config.get("version") or config.get("version_info")
    if not raw:
        return None
    match = _VERSION_RE.match(raw)
    return match.group(1) if match else raw


class VenvDetector:
    """Turns located candidates into enriched :class:`Venv` instances.

    Package inspection and classification are delegated to injected
    strategies; an optional :class:`VenvCache` avoids re-inspecting unchanged
    environments.
    """

    def __init__(
        self,
        locator: VenvLocator,
        inspector: PackageInspector,
        classifier: CategoryClassifier,
        cache: VenvCache | None = None,
    ) -> None:
        self.locator = locator
        self.inspector = inspector
        self.classifier = classifier
        self.cache = cache

    def detect(self) -> list:
        """Locate and build every virtual environment."""
        venvs = [self.build(path) for path in self.locator.locate()]
        if self.cache is not None:
            self.cache.save()
        return venvs

    def build(self, venv_path: Path) -> Venv:
        """Resolve a single (already validated) virtual environment."""
        venv_path = Path(venv_path)
        fingerprint = self._fingerprint(venv_path) if self.cache is not None else None
        if self.cache is not None and fingerprint is not None:
            cached = self.cache.get(venv_path, fingerprint)
            if cached is not None:
                return cached

        packages = self.inspector.list_packages(venv_path)
        venv = Venv(
            path=venv_path,
            packages=packages,
            python_version=python_version(venv_path),
            categories=self.classifier.classify(venv_path, packages),
        )
        if self.cache is not None and fingerprint is not None:
            self.cache.put(venv, fingerprint)
        return venv

    @staticmethod
    def _fingerprint(venv_path: Path) -> str:
        parts = [pyvenv_cfg(venv_path) or venv_path, find_site_packages(venv_path) or venv_path]
        return stat_fingerprint(*parts)
