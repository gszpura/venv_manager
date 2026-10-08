"""On-disk cache of resolved virtual environments.

The cache is a dumb keyed store: callers supply a *fingerprint* (a string that
changes whenever the environment's contents change) and the cache returns the
previously resolved :class:`Venv` only when the fingerprint still matches.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Self

from vvm.models import Venv, VenvCategory

_SCHEMA = 1


def stat_fingerprint(*paths: Path) -> str:
    """Build a fingerprint string from the stat of the given paths."""
    parts = []
    for raw in paths:
        path = Path(raw)
        try:
            stat = path.stat()
        except OSError:
            parts.append(f"{path}:missing")
        else:
            parts.append(f"{path}:{stat.st_mtime_ns}:{stat.st_size}")
    return "|".join(parts)


class VenvCache:
    """JSON-backed cache mapping venv paths to resolved :class:`Venv` objects."""

    def __init__(self, path: Path) -> None:
        self.path = Path(path)
        self._entries: dict[str, dict] = {}
        self._dirty = False
        self._load()

    def get(self, path: Path, fingerprint: str) -> Venv | None:
        entry = self._entries.get(str(Path(path)))
        if not entry or entry.get("fingerprint") != fingerprint:
            return None
        return Venv(
            path=Path(path),
            packages=frozenset(entry.get("packages", [])),
            python_version=entry.get("python_version"),
            categories=tuple(VenvCategory(value) for value in entry.get("categories", [])),
        )

    def put(self, venv: Venv, fingerprint: str) -> None:
        self._entries[str(venv.path)] = {
            "fingerprint": fingerprint,
            "python_version": venv.python_version,
            "packages": sorted(venv.packages),
            "categories": [category.value for category in venv.categories],
        }
        self._dirty = True

    def prune(self, keep_paths: Iterable[Path]) -> None:
        """Drop entries whose path is not in ``keep_paths``."""
        keep = {str(Path(path)) for path in keep_paths}
        for key in list(self._entries):
            if key not in keep:
                del self._entries[key]
                self._dirty = True

    def save(self) -> None:
        if not self._dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {"schema": _SCHEMA, "venvs": self._entries}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True))
        self._dirty = False

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            raw = json.loads(self.path.read_text())
        except (OSError, ValueError):
            return
        if isinstance(raw, dict) and raw.get("schema") == _SCHEMA:
            self._entries = raw.get("venvs", {})

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.save()
