from pathlib import Path

from vvm.matching import MinimalCoverageScoring, NameComparator, VenvMatcher
from vvm.models import Requirement, Venv

FLAKE_REQS = [Requirement(name="flask"), Requirement(name="requests")]
VENVS = [
    Venv(Path("/complete-small"), frozenset({"flask", "requests"})),
    Venv(Path("/complete-big"), frozenset({"flask", "requests", "numpy", "pandas"})),
    Venv(Path("/missing-one"), frozenset({"flask", "numpy"})),
    Venv(Path("/missing-both"), frozenset({"numpy"})),
]


def test_name_comparator():
    comparator = NameComparator()
    venv = Venv(Path("/v"), frozenset({"flask"}))
    assert comparator.satisfied_by(Requirement(name="flask"), venv.packages)
    assert not comparator.satisfied_by(Requirement(name="django"), venv.packages)


def test_ranking_complete_then_closest():
    results = VenvMatcher().match(FLAKE_REQS, VENVS)
    assert [str(r.venv.path) for r in results] == [
        "/complete-small",
        "/complete-big",
        "/missing-one",
        "/missing-both",
    ]
    assert results[0].is_complete
    assert results[2].missing == frozenset({"requests"})


def test_best_and_empty_inputs():
    matcher = VenvMatcher()
    assert str(matcher.best(FLAKE_REQS, VENVS).venv.path) == "/complete-small"
    assert matcher.best(FLAKE_REQS, []) is None


def test_empty_requirements_pick_smallest():
    assert str(VenvMatcher().best([], VENVS).venv.path) == "/missing-both"


def test_generator_input_is_consumed_once():
    matcher = VenvMatcher()
    results = matcher.match((r for r in FLAKE_REQS), VENVS)
    assert len(results) == len(VENVS)


def test_scoring_strategy_is_injectable():
    class AlwaysEqual(MinimalCoverageScoring):
        def score(self, missing, extra, venv):
            return (0,)

    results = VenvMatcher(scoring=AlwaysEqual()).match(FLAKE_REQS, VENVS)
    assert len(results) == len(VENVS)
