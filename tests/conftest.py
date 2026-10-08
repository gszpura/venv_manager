import sys
from pathlib import Path

import pytest


@pytest.fixture
def make_venv(tmp_path):
    """Create a minimal but structurally valid virtual environment."""

    def _make(name, packages=(), version="3.11.5"):
        root = Path(tmp_path) / name
        (root / "bin").mkdir(parents=True, exist_ok=True)
        (root / "bin" / "python").symlink_to(sys.executable)
        (root / "lib" / "python3.11" / "site-packages").mkdir(parents=True, exist_ok=True)
        (root / "pyvenv.cfg").write_text(f"version = {version}\nhome = {sys.prefix}\n")
        return root

    return _make
