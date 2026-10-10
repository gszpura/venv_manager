"""Assemble a :class:`VenvDetector` from configuration and its collaborators."""

from __future__ import annotations

from pathlib import Path

from vvm.cache import VenvCache
from vvm.config import Config
from vvm.detection.detector import VenvDetector
from vvm.detection.locator import (
    ConfiguredDirStrategy,
    CurrentDirStrategy,
    VenvLocator,
)
from vvm.inspection import DefaultCategoryClassifier, ImportlibMetadataInspector


def build_detector(config: Config, directory: Path, *, use_cache: bool = True) -> VenvDetector:
    """Create a detector for ``directory`` using ``config``.

    The current-directory strategy targets ``directory`` (typically the project
    being searched) while the configured strategy scans ``config.search_dirs``.
    """
    strategies = [
        CurrentDirStrategy(directory, config.venv_names),
        ConfiguredDirStrategy(config.search_dirs, max_depth=config.search_depth),
    ]
    cache = VenvCache(config.cache_path) if use_cache else None
    return VenvDetector(
        VenvLocator(strategies),
        ImportlibMetadataInspector(),
        DefaultCategoryClassifier(),
        cache,
    )
