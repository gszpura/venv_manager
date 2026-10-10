import io
from pathlib import Path

import pytest

from vvm.actions import Action, BestAction, ConfigAction, DetectAction, UnlinkAction
from vvm.actions.config import _SEPARATOR
from vvm.config import Config
from vvm.linking import SymlinkLinker
from vvm.manager import VenvManager
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


def test_actions_inherit_base():
    assert issubclass(DetectAction, Action)
    assert issubclass(BestAction, Action)
    assert issubclass(ConfigAction, Action)


def test_build_factories_return_actions(tmp_path):
    config = Config.from_mapping({"cache_path": str(tmp_path / "c.json")})
    assert isinstance(DetectAction.build(config, directory=tmp_path, use_cache=False), DetectAction)
    assert isinstance(BestAction.build(config, project_dir=tmp_path, use_cache=False), BestAction)
    assert isinstance(ConfigAction.build(config, config_path=tmp_path / "config.toml"), ConfigAction)
    assert isinstance(UnlinkAction.build(config, project_dir=tmp_path), UnlinkAction)


def test_manager_registers_default_actions():
    manager = VenvManager(config=Config.from_mapping({}))
    assert set(manager.actions) == {"detect", "best", "unlink", "config"}


def test_manager_unknown_action_raises():
    manager = VenvManager(config=Config.from_mapping({}))
    with pytest.raises(ValueError):
        manager.run("nope")


def test_config_action_shows_path_content_and_defaults(tmp_path, capsys):
    config = tmp_path / "config.toml"
    config.write_text('search_dirs = ["/x"]\n')
    assert ConfigAction(config, [Path("/a"), Path("/b")]).run() == 0
    out = capsys.readouterr().out
    assert f"Config path: {config}" in out
    assert 'search_dirs = ["/x"]' in out
    assert "Config content:" in out
    assert "Default search paths:" in out
    assert "\n/a\n/b\n" in out
    assert out.count(_SEPARATOR) == 2


def test_config_action_missing_file_has_empty_content(tmp_path, capsys):
    missing = tmp_path / "nope.toml"
    assert ConfigAction(missing, [Path("/a")]).run() == 0
    out = capsys.readouterr().out
    assert f"Config path: {missing}" in out
    assert f"Config content:\n\n{_SEPARATOR}" in out


def test_unlink_action_removes_link(tmp_path, capsys):
    source = tmp_path / "real"
    source.mkdir()
    target = tmp_path / ".venv"
    target.symlink_to(source)
    assert UnlinkAction(SymlinkLinker(), project_dir=tmp_path).run() == 0
    assert not target.exists()
    assert "Removed" in capsys.readouterr().out


def test_unlink_action_without_link(tmp_path, capsys):
    assert UnlinkAction(SymlinkLinker(), project_dir=tmp_path).run() == 1
    assert "No link found" in capsys.readouterr().out


def test_unlink_action_refuses_non_link(tmp_path, capsys):
    target = tmp_path / ".venv"
    target.mkdir()
    assert UnlinkAction(SymlinkLinker(), project_dir=tmp_path).run() == 1
    assert "non-symlink" in capsys.readouterr().out
    assert target.is_dir()


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
