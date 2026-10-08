"""Installed-package inspection strategies."""

from __future__ import annotations

import json
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path

from vvm.inspection.paths import find_python
from vvm.models import normalize_name

_LIST_SCRIPT = (
    "import importlib.metadata as md, json\n"
    "names = {d.metadata['Name'] for d in md.distributions() if d.metadata['Name']}\n"
    "print(json.dumps(sorted(names)))\n"
)


class PackageInspector(ABC):
    """Reports the distribution names installed in a virtual environment."""

    @abstractmethod
    def list_packages(self, venv_path: Path) -> frozenset:
        """Return PEP 503 normalized package names, or empty on failure."""


class ImportlibMetadataInspector(PackageInspector):
    """Runs the venv interpreter and reads ``importlib.metadata``.

    Requires no ``pip`` inside the environment and works across platforms.
    """

    def __init__(self, timeout: float = 30.0) -> None:
        self.timeout = timeout

    def list_packages(self, venv_path: Path) -> frozenset:
        python = find_python(venv_path)
        if python is None:
            return frozenset()
        try:
            completed = subprocess.run(
                [str(python), "-c", _LIST_SCRIPT],
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            return frozenset()
        if completed.returncode != 0:
            return frozenset()
        try:
            names = json.loads(completed.stdout)
        except ValueError:
            return frozenset()
        return frozenset(normalize_name(name) for name in names)
