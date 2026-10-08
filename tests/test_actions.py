import io
from pathlib import Path

from vvm.actions import BestAction, DetectAction
from vvm.linking import SymlinkLinker
from vvm.matching import VenvMatcher
from vvm.models import Requirement, Venv


class StubDetector:
    def __init__(self, venvs):
        self._venvs = list(venvs)

    def detect(self):
        return list(self._venvs)


class StubReader:
    def __init__(self, requirements):
        self._requirements = requirements

    def read(self, project_dir):
        return self._requirements


class Requirements:
    def __init__(self, names):
        self.source = Path("requirements.txt")
        self.requirements = [Requirement(name=name) for name in names]
        self.names = frozenset(name.lower() for name in names)


SMALL = Venv(Path("/v/small"), frozenset({"flask", "requests"}))
BIG = Venv(Path("/v/big"), frozenset({"flask", "requests", "numpy"}))


def test_detect_action_lists_venvs(capsys):
    assert DetectAction(StubDetector([SMALL, BIG])).run() == 0
    out = capsys.readouterr().out
    assert "/v/small [unknown] 2 packages" in out
    assert "/v/big [unknown] 3 packages" in out


def test_detect_action_empty(capsys):
    assert DetectAction(StubDetector([])).run() == 0
    assert "No virtual environments found." in capsys.readouterr().out


class NoneReader:
    def read(self, project_dir):
        return None


def test_best_action_without_requirements(tmp_path):
    action = BestAction(StubDetector([SMALL]), NoneReader(), VenvMatcher(), project_dir=tmp_path)
    assert action.run() == 1


def test_best_action_links_complete(tmp_path):
    action = BestAction(
        StubDetector([SMALL, BIG]),
        StubReader(Requirements(["flask", "requests"])),
        VenvMatcher(),
        SymlinkLinker(),
        project_dir=tmp_path,
    )
    assert action.run() == 0
    assert (tmp_path / ".venv").resolve() == Path("/v/small").resolve()


def test_best_action_reports_missing(tmp_path):
    out = io.StringIO()
    action = BestAction(
        StubDetector([SMALL]),
        StubReader(Requirements(["flask", "django"])),
        VenvMatcher(),
        SymlinkLinker(),
        project_dir=tmp_path,
        out=out,
    )
    assert action.run() == 1
    assert "missing 1: django" in out.getvalue()
    assert not (tmp_path / ".venv").exists()
