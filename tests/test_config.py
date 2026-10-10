import os
import sys

from vvm.config import Config, ConfigLoader

_TOOL_ENV_VARS = (
    "WORKON_HOME",
    "POETRY_VIRTUALENVS_PATH",
    "POETRY_CACHE_DIR",
    "PIPX_HOME",
    "PYENV_ROOT",
    "CONDA_ENVS_PATH",
    "MAMBA_ROOT_PREFIX",
    "XDG_DATA_HOME",
    "XDG_CACHE_HOME",
    "XDG_CONFIG_HOME",
)


def _isolate(monkeypatch, tmp_path, platform="linux"):
    monkeypatch.setenv("HOME", str(tmp_path))
    for name in _TOOL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(sys, "platform", platform)


def test_defaults():
    config = Config.from_mapping({})
    assert config.venv_names[0] == ".venv"
    assert "pyproject.toml" in config.project_files
    assert config.cache_path.name == "venvs.json"
    assert config.search_dirs
    assert config.search_depth == 3


def test_search_depth_is_configurable():
    assert Config.from_mapping({"search_depth": 5}).search_depth == 5
    assert Config.from_mapping({"search_depth": 0}).search_depth == 1


def test_categories_empty_without_config():
    assert Config.from_mapping({}).categories == ()


def test_categories_are_parsed_in_order():
    config = Config.from_mapping(
        {"categories": {"server": ["flask"], "ai": ["torch"], "other": []}}
    )
    assert [rule.name for rule in config.categories] == ["server", "ai", "other"]
    assert config.categories[0].packages == frozenset({"flask"})
    assert config.categories[2].packages == frozenset()


def test_malformed_category_entries_are_skipped():
    config = Config.from_mapping({"categories": {"ai": "torch", "ok": ["Pandas"]}})
    assert [rule.name for rule in config.categories] == ["ok"]
    assert config.categories[0].packages == frozenset({"pandas"})


def test_default_search_dirs_cover_common_tools(tmp_path, monkeypatch):
    _isolate(monkeypatch, tmp_path)
    dirs = {str(p) for p in Config.from_mapping({}).search_dirs}
    for expected in (
        ".virtualenvs",
        ".local/share/virtualenvs",
        ".cache/pypoetry/virtualenvs",
        ".local/share/pdm/venvs",
        ".local/share/pipx/venvs",
        ".pyenv/versions",
        ".conda/envs",
        "miniconda3/envs",
        "anaconda3/envs",
        "micromamba/envs",
        ".local/share/mamba/envs",
        ".local/share/hatch/env/virtual",
    ):
        assert str(tmp_path / expected) in dirs


def test_default_search_dirs_honor_env_overrides(tmp_path, monkeypatch):
    _isolate(monkeypatch, tmp_path)
    monkeypatch.setenv("WORKON_HOME", str(tmp_path / "wh"))
    monkeypatch.setenv("POETRY_VIRTUALENVS_PATH", str(tmp_path / "poetry"))
    monkeypatch.setenv("PIPX_HOME", str(tmp_path / "pipx"))
    monkeypatch.setenv("PYENV_ROOT", str(tmp_path / "pyenv"))
    monkeypatch.setenv("MAMBA_ROOT_PREFIX", str(tmp_path / "mamba"))
    monkeypatch.setenv("CONDA_ENVS_PATH", os.pathsep.join([str(tmp_path / "c1"), str(tmp_path / "c2")]))
    dirs = {str(p) for p in Config.from_mapping({}).search_dirs}
    assert str(tmp_path / "wh") in dirs
    assert str(tmp_path / "poetry") in dirs
    assert str(tmp_path / "pipx" / "venvs") in dirs
    assert str(tmp_path / "pyenv" / "versions") in dirs
    assert str(tmp_path / "mamba" / "micromamba" / "envs") in dirs
    assert str(tmp_path / "c1") in dirs
    assert str(tmp_path / "c2") in dirs


def test_default_search_dirs_macos(tmp_path, monkeypatch):
    _isolate(monkeypatch, tmp_path, platform="darwin")
    dirs = {str(p) for p in Config.from_mapping({}).search_dirs}
    assert str(tmp_path / "Library/Caches/pypoetry/virtualenvs") in dirs
    assert str(tmp_path / "Library/Application Support/pdm/venvs") in dirs
    assert str(tmp_path / "Library/Application Support/pipx/venvs") in dirs
    assert str(tmp_path / "Library/Application Support/hatch/env/virtual") in dirs


def test_from_mapping_expands_and_dedupes():
    config = Config.from_mapping(
        {
            "search_dirs": ["~/foo", "~/foo", "/tmp/bar"],
            "cache_path": "~/c.json",
            "venv_names": [".venv"],
        }
    )
    assert [str(p) for p in config.search_dirs] == [
        str(config.search_dirs[0]),
        "/tmp/bar",
    ]
    assert len(config.search_dirs) == 2
    assert config.cache_path.name == "c.json"
    assert config.venv_names == (".venv",)


def test_loader_reads_file(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('search_dirs = ["/only/here"]\n')
    config = ConfigLoader(config_file).load()
    assert [str(p) for p in config.search_dirs] == ["/only/here"]


def test_loader_creates_default_config_with_categories(tmp_path):
    config_file = tmp_path / "vvm" / "config.toml"
    config = ConfigLoader(config_file).load()
    assert config_file.is_file()
    assert [rule.name for rule in config.categories] == ["ai", "data_science", "server", "other"]
    assert "torch" in config.categories[0].packages
    assert config.categories[-1].packages == frozenset()


def test_loader_existing_file_without_categories_is_empty(tmp_path):
    config_file = tmp_path / "config.toml"
    config_file.write_text('search_dirs = ["/only/here"]\n')
    config = ConfigLoader(config_file).load()
    assert config.categories == ()


def test_loader_missing_file_creates_and_uses_defaults(tmp_path):
    config_file = tmp_path / "nope.toml"
    config = ConfigLoader(config_file).load()
    assert config_file.is_file()
    assert config.search_dirs
