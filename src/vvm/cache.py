"""On-disk cache of resolved virtual environments.

The cache is a dumb keyed store: callers supply a *fingerprint* (a string that
changes whenever the environment's contents change) and the cache returns the
previously resolved :class:`Venv` only when the fingerprint still matches.

The cache is also temporary: the time it was written is stored alongside the
entries, and once it is older than :data:`DEFAULT_MAX_AGE` seconds the whole
cache is ignored and regenerated.
"""

from __future__ import annotations

import json
import time
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import Self

from vvm.models import Venv

_SCHEMA = 2
DEFAULT_MAX_AGE = 300.0


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

    def __init__(
        self,
        path: Path,
        max_age: float = DEFAULT_MAX_AGE,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self.path = Path(path)
        self.max_age = max_age
        self._clock = clock
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
            categories=tuple(str(value) for value in entry.get("categories", [])),
        )

    def put(self, venv: Venv, fingerprint: str) -> None:
        self._entries[str(venv.path)] = {
            "fingerprint": fingerprint,
            "python_version": venv.python_version,
            "packages": sorted(venv.packages),
            "categories": list(venv.categories),
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
        payload = {"schema": _SCHEMA, "generated_at": self._clock(), "venvs": self._entries}
        self.path.write_text(json.dumps(payload, indent=2, sort_keys=True))
        self._dirty = False

    def _load(self) -> None:
        if not self.path.is_file():
            return
        try:
            raw = json.loads(self.path.read_text())
        except (OSError, ValueError):
            return
        if not isinstance(raw, dict) or raw.get("schema") != _SCHEMA:
            return
        generated_at = raw.get("generated_at")
        if not isinstance(generated_at, (int, float)):
            return
        if self._clock() - generated_at > self.max_age:
            return
        self._entries = raw.get("venvs", {})

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.save()
