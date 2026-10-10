"""Upper-layer facade that wires collaborators and dispatches features.

``VenvManager`` is the composition root: it builds the shared services
(inspector, classifier, cache) once and creates a *fresh* detector per
invocation, because the current-directory strategy depends on the directory
being searched.
"""

from __future__ import annotations

from pathlib import Path
from typing import TextIO

from vvm.actions import (
    BestAction,
    ConfigAction,
    DetectAction,
    PlainVenvFormatter,
    VenvFormatter,
)
from vvm.cache import VenvCache
from vvm.config import Config, ConfigLoader
from vvm.detection import (
    ConfiguredDirStrategy,
    CurrentDirStrategy,
    VenvDetector,
    VenvLocator,
)
from vvm.inspection import (
    CategoryClassifier,
    DefaultCategoryClassifier,
    ImportlibMetadataInspector,
    PackageInspector,
)
from vvm.linking import SymlinkLinker, VenvLinker
from vvm.matching import VenvMatcher
from vvm.models import Venv
from vvm.requirements import ProjectRequirementsReader, default_reader


class VenvManager:
    """Feature facade for the CLI and library consumers."""

    def __init__(
        self,
        config: Config | None = None,
        inspector: PackageInspector | None = None,
        classifier: CategoryClassifier | None = None,
        matcher: VenvMatcher | None = None,
        reader: ProjectRequirementsReader | None = None,
        linker: VenvLinker | None = None,
        formatter: VenvFormatter | None = None,
        cache: VenvCache | None = None,
        use_cache: bool = True,
        config_path: Path | None = None,
    ) -> None:
        if config is not None:
            self.config = config
            self.config_path = (
                Path(config_path).expanduser() if config_path is not None else ConfigLoader.default_path()
            )
        else:
            loader = ConfigLoader(config_path)
            self.config = loader.load()
            self.config_path = loader.path
        self.inspector = inspector or ImportlibMetadataInspector()
        self.classifier = classifier or DefaultCategoryClassifier()
        self.matcher = matcher or VenvMatcher()
        self.reader = reader or default_reader(self.config.project_files)
        self.linker = linker or SymlinkLinker()
        self.formatter = formatter or PlainVenvFormatter()
        if cache is not None:
            self.cache: VenvCache | None = cache
        elif use_cache:
            self.cache = VenvCache(self.config.cache_path)
        else:
            self.cache = None

    def detector_for(self, directory: Path) -> VenvDetector:
        """Build a detector whose current-dir strategy targets ``directory``."""
        strategies = [
            CurrentDirStrategy(directory, self.config.venv_names),
            ConfiguredDirStrategy(self.config.search_dirs, max_depth=self.config.search_depth),
        ]
        return VenvDetector(VenvLocator(strategies), self.inspector, self.classifier, self.cache)

    def find_venvs(self, directory: Path | None = None) -> list[Venv]:
        """Return every detected venv for ``directory`` (default: cwd)."""
        target = Path(directory) if directory is not None else Path.cwd()
        return self.detector_for(target).detect()

    def detect(self, directory: Path | None = None, out: TextIO | None = None) -> int:
        """Run the ``detect`` feature and return its exit code."""
        target = Path(directory) if directory is not None else Path.cwd()
        return DetectAction(self.detector_for(target), self.formatter, out).run()

    def show_config(self, out: TextIO | None = None) -> int:
        """Run the ``config`` feature and return its exit code."""
        action = ConfigAction(
            config_path=self.config_path,
            default_search_dirs=Config.from_mapping({}).search_dirs,
            out=out,
        )
        return action.run()

    def best(
        self,
        project_dir: Path | None = None,
        link: bool = True,
        force: bool = False,
        link_name: str = ".venv",
        out: TextIO | None = None,
    ) -> int:
        """Run the ``best`` feature and return its exit code."""
        target = Path(project_dir) if project_dir is not None else Path.cwd()
        action = BestAction(
            detector=self.detector_for(target),
            reader=self.reader,
            matcher=self.matcher,
            linker=self.linker,
            project_dir=target,
            link=link,
            force=force,
            link_name=link_name,
            out=out,
        )
        return action.run()
