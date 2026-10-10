from vvm.cache import VenvCache
from vvm.detection import (
    ConfiguredDirStrategy,
    CurrentDirStrategy,
    VenvDetector,
    VenvLocator,
    python_version,
)
from vvm.inspection import (
    CategoryClassifier,
    DefaultCategoryClassifier,
    PackageInspector,
)
from vvm.models import UNKNOWN_CATEGORY, CategoryRule


class FakeInspector(PackageInspector):
    def __init__(self, mapping):
        self.mapping = mapping
        self.calls = []

    def list_packages(self, venv_path):
        self.calls.append(str(venv_path))
        return frozenset(self.mapping.get(venv_path.name, ()))


class RecordingClassifier(CategoryClassifier):
    def __init__(self):
        self.calls = 0

    def classify(self, venv_path, packages):
        self.calls += 1
        return (UNKNOWN_CATEGORY,)


def test_current_dir_strategy(make_venv):
    root = make_venv(".venv").parent
    located = list(CurrentDirStrategy(root, [".venv", "venv"]).locate())
    assert [p.name for p in located] == [".venv", "venv"]


def test_locator_filters_and_dedupes(make_venv):
    root = make_venv("envs")
    venv = make_venv("envs/a")
    (root / "notavenv").mkdir()
    locator = VenvLocator([ConfiguredDirStrategy([root]), ConfiguredDirStrategy([root])])
    assert locator.locate() == [venv]


def test_configured_strategy_is_flat_by_default(make_venv, tmp_path):
    make_venv("scope/project/env/hash")
    assert list(ConfiguredDirStrategy([tmp_path / "scope"]).locate()) == []


def test_configured_strategy_recurses_to_nested_venvs(make_venv, tmp_path):
    nested = make_venv("scope/project/env/hash")
    strategy = ConfiguredDirStrategy([tmp_path / "scope"], max_depth=3)
    assert list(strategy.locate()) == [nested]


def test_configured_strategy_prunes_inside_detected_venv(make_venv, tmp_path):
    outer = make_venv("scope/outer")
    make_venv("scope/outer/inner")
    strategy = ConfiguredDirStrategy([tmp_path / "scope"], max_depth=3)
    assert list(strategy.locate()) == [outer]


def test_python_version(make_venv):
    assert python_version(make_venv("e", version="3.9.16.final.0")) == "3.9.16"


def test_detector_builds_and_caches(make_venv, tmp_path):
    venv = make_venv(".venv")
    inspector = FakeInspector({".venv": {"flask", "requests"}})
    classifier = RecordingClassifier()
    cache = VenvCache(tmp_path / "cache.json")
    detector = VenvDetector(VenvLocator([CurrentDirStrategy(venv.parent, [".venv"])]), inspector, classifier, cache)

    result = detector.detect()
    assert len(result) == 1
    assert result[0].packages == frozenset({"flask", "requests"})
    assert result[0].python_version == "3.11.5"
    assert classifier.calls == 1

    detector.detect()  # second run served from cache
    assert classifier.calls == 1
    assert inspector.calls == [str(venv)]


def test_cache_invalidated_when_category_rules_change(make_venv, tmp_path):
    venv = make_venv(".venv")
    inspector = FakeInspector({".venv": {"torch"}})
    locator = VenvLocator([CurrentDirStrategy(venv.parent, [".venv"])])
    cache_path = tmp_path / "cache.json"

    unknown = VenvDetector(locator, inspector, DefaultCategoryClassifier(), VenvCache(cache_path))
    assert unknown.detect()[0].primary_category == UNKNOWN_CATEGORY

    rules = (CategoryRule("ai", frozenset({"torch"})), CategoryRule("other", frozenset()))
    classified = VenvDetector(locator, inspector, DefaultCategoryClassifier(rules), VenvCache(cache_path))
    assert classified.detect()[0].primary_category == "ai"
