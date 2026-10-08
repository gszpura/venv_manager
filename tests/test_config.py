from vvm.config import Config, ConfigLoader


def test_defaults():
    config = Config.from_mapping({})
    assert config.venv_names[0] == ".venv"
    assert "pyproject.toml" in config.project_files
    assert config.cache_path.name == "venvs.json"
    assert config.search_dirs


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


def test_loader_missing_file_uses_defaults(tmp_path):
    config = ConfigLoader(tmp_path / "nope.toml").load()
    assert config.search_dirs
