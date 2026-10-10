from pathlib import Path

from vvm.cache import VenvCache, stat_fingerprint
from vvm.models import UNKNOWN_CATEGORY, Venv


def _venv():
    return Venv(
        path=Path("/v/.venv"),
        packages=frozenset({"flask", "requests"}),
        python_version="3.11.5",
        categories=(UNKNOWN_CATEGORY,),
    )


def test_round_trip(tmp_path):
    path = tmp_path / "cache.json"
    with VenvCache(path) as cache:
        assert cache.get(Path("/v/.venv"), "fp") is None
        cache.put(_venv(), "fp")
    assert VenvCache(path).get(Path("/v/.venv"), "fp") == _venv()


def test_stale_fingerprint_misses(tmp_path):
    cache = VenvCache(tmp_path / "cache.json")
    cache.put(_venv(), "fp1")
    assert cache.get(Path("/v/.venv"), "fp2") is None


def test_prune(tmp_path):
    cache = VenvCache(tmp_path / "cache.json")
    cache.put(_venv(), "fp")
    cache.prune([])
    assert cache.get(Path("/v/.venv"), "fp") is None


def test_malformed_file_is_ignored(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text("{ not json")
    assert VenvCache(path).get(Path("/v/.venv"), "fp") is None


def test_cache_is_temporary(tmp_path):
    path = tmp_path / "cache.json"
    now = {"value": 1000.0}
    cache = VenvCache(path, max_age=300, clock=lambda: now["value"])
    cache.put(_venv(), "fp")
    cache.save()

    now["value"] += 299
    assert VenvCache(path, max_age=300, clock=lambda: now["value"]).get(Path("/v/.venv"), "fp") == _venv()

    now["value"] += 2
    assert VenvCache(path, max_age=300, clock=lambda: now["value"]).get(Path("/v/.venv"), "fp") is None


def test_cache_without_timestamp_is_ignored(tmp_path):
    path = tmp_path / "cache.json"
    path.write_text('{"schema": 2, "venvs": {"/v/.venv": {"fingerprint": "fp"}}}')
    assert VenvCache(path).get(Path("/v/.venv"), "fp") is None


def test_stat_fingerprint(tmp_path):
    present = tmp_path / "a"
    present.write_text("x")
    fingerprint = stat_fingerprint(present, tmp_path / "missing")
    assert "missing" in fingerprint
