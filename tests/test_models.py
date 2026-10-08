from pathlib import Path

from vvm.models import MatchResult, Requirement, Venv, VenvCategory, normalize_name


def test_normalize_name():
    assert normalize_name("Django_Rest.Framework") == "django-rest-framework"
    assert normalize_name("zope.interface") == "zope-interface"


def test_requirement_normalizes_name():
    assert Requirement(name="Requests").name == "requests"


def test_venv_properties():
    venv = Venv(path=Path("/x/.venv"), packages=frozenset({"a", "b"}), python_version="3.11.5")
    assert venv.name == ".venv"
    assert venv.package_count == 2
    assert venv.primary_category is VenvCategory.UNKNOWN


def test_match_result():
    venv = Venv(path=Path("/v"))
    assert MatchResult(venv=venv).is_complete
    result = MatchResult(venv=venv, missing=frozenset({"a"}), extra=frozenset({"b", "c"}))
    assert not result.is_complete
    assert result.extra_count == 2
