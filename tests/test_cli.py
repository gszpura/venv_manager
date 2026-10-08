import pytest

from vvm.cli import build_parser, main


def _config(tmp_path, search_dir):
    config = tmp_path / "config.toml"
    config.write_text(
        f'search_dirs = ["{search_dir}"]\ncache_path = "{tmp_path / "cache.json"}"\n'
    )
    return config


def test_version(capsys):
    with pytest.raises(SystemExit):
        main(["--version"])
    assert "vvm 0.1.0" in capsys.readouterr().out


def test_requires_subcommand():
    with pytest.raises(SystemExit):
        main([])


def test_detect_no_venvs(tmp_path, capsys):
    empty = tmp_path / "empty"
    empty.mkdir()
    project = tmp_path / "proj"
    project.mkdir()
    config = _config(tmp_path, empty)
    assert main(["detect", "-C", str(project), "--config", str(config)]) == 0
    assert "No virtual environments found." in capsys.readouterr().out


def test_best_without_requirements_returns_one(tmp_path, capsys):
    empty = tmp_path / "empty"
    empty.mkdir()
    project = tmp_path / "proj"
    project.mkdir()
    config = _config(tmp_path, empty)
    assert main(["best", "-C", str(project), "--config", str(config)]) == 1
    assert "No project requirements found" in capsys.readouterr().out


def test_common_options_accepted_before_and_after_subcommand(tmp_path):
    parser = build_parser()
    after = parser.parse_args(["detect", "-C", "/x", "--config", "/c"])
    assert after.directory == "/x" and after.config == "/c"
    before = parser.parse_args(["-C", "/x", "--config", "/c", "detect"])
    assert before.directory == "/x" and before.config == "/c"
