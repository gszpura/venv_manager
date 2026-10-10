import pytest

from vvm.linking import LinkingError, SymlinkLinker
from vvm.models import Venv


@pytest.fixture
def linker():
    return SymlinkLinker()


def test_creates_symlink(tmp_path, linker):
    source = tmp_path / "real"
    source.mkdir()
    target = tmp_path / "proj" / ".venv"
    assert linker.link(Venv(path=source), target) == target
    assert target.is_symlink()
    assert target.resolve() == source.resolve()


def test_idempotent(tmp_path, linker):
    source = tmp_path / "real"
    source.mkdir()
    target = tmp_path / ".venv"
    linker.link(Venv(path=source), target)
    linker.link(Venv(path=source), target)
    assert target.is_symlink()


def test_conflict_requires_force(tmp_path, linker):
    source = tmp_path / "a"
    source.mkdir()
    other = tmp_path / "b"
    other.mkdir()
    target = tmp_path / ".venv"
    linker.link(Venv(path=source), target)
    with pytest.raises(LinkingError):
        linker.link(Venv(path=other), target)
    linker.link(Venv(path=other), target, force=True)
    assert target.resolve() == other.resolve()


def test_refuses_non_empty_directory(tmp_path, linker):
    source = tmp_path / "real"
    source.mkdir()
    target = tmp_path / "dir"
    target.mkdir()
    (target / "keep").write_text("data")
    with pytest.raises(LinkingError):
        linker.link(Venv(path=source), target, force=True)


def test_replaces_empty_directory(tmp_path, linker):
    source = tmp_path / "real"
    source.mkdir()
    target = tmp_path / "dir"
    target.mkdir()
    linker.link(Venv(path=source), target, force=True)
    assert target.is_symlink()


def test_unlink_removes_symlink(tmp_path, linker):
    source = tmp_path / "real"
    source.mkdir()
    target = tmp_path / ".venv"
    linker.link(Venv(path=source), target)
    assert linker.unlink(target) == target
    assert not target.exists()
    assert not target.is_symlink()


def test_unlink_missing_returns_none(tmp_path, linker):
    assert linker.unlink(tmp_path / ".venv") is None


def test_unlink_refuses_non_symlink(tmp_path, linker):
    target = tmp_path / ".venv"
    target.mkdir()
    with pytest.raises(LinkingError):
        linker.unlink(target)
    assert target.is_dir()
