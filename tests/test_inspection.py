from vvm.inspection import (
    DefaultCategoryClassifier,
    find_python,
    find_site_packages,
    is_venv,
    read_pyvenv_cfg,
)
from vvm.models import UNKNOWN_CATEGORY, CategoryRule

RULES = (
    CategoryRule("ai", frozenset({"torch", "tensorflow"})),
    CategoryRule("data_science", frozenset({"pandas"})),
    CategoryRule("server", frozenset({"flask"})),
    CategoryRule("other", frozenset()),
)


def test_detect_venv_layout(make_venv):
    venv = make_venv(".venv")
    assert is_venv(venv)
    assert find_python(venv) == venv / "bin" / "python"
    assert find_site_packages(venv) == venv / "lib" / "python3.11" / "site-packages"
    assert read_pyvenv_cfg(venv)["version"] == "3.11.5"


def test_non_venv(tmp_path):
    assert not is_venv(tmp_path)
    assert find_python(tmp_path) is None
    assert find_site_packages(tmp_path) is None


def test_default_classifier_without_rules(make_venv):
    venv = make_venv("env")
    assert DefaultCategoryClassifier().classify(venv, frozenset()) == (UNKNOWN_CATEGORY,)


def test_classifier_uses_rule_order(make_venv):
    venv = make_venv("env")
    classifier = DefaultCategoryClassifier(RULES)
    assert classifier.classify(venv, frozenset({"torch", "pandas"})) == ("ai",)
    assert classifier.classify(venv, frozenset({"pandas"})) == ("data_science",)
    assert classifier.classify(venv, frozenset({"flask"})) == ("server",)


def test_classifier_falls_back_to_catch_all(make_venv):
    venv = make_venv("env")
    classifier = DefaultCategoryClassifier(RULES)
    assert classifier.classify(venv, frozenset({"requests"})) == ("other",)
    assert classifier.classify(venv, frozenset()) == ("other",)
