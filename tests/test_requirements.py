from vvm.requirements import (
    PyprojectParser,
    RequirementsTxtParser,
    default_reader,
    parse_requirement,
)


def test_parse_requirement_variants():
    assert parse_requirement("requests>=2.0").name == "requests"
    requirement = parse_requirement('Django[argon2]>=4 ; python_version>="3.10"')
    assert requirement.name == "django"
    assert requirement.specifier == ">=4"
    assert requirement.extras == frozenset({"argon2"})
    assert parse_requirement("name @ https://x/y.whl").specifier is None
    assert parse_requirement("# comment") is None
    assert parse_requirement("-e ./local") is None


def test_requirements_txt_includes_and_dedupes(tmp_path):
    (tmp_path / "reqs.txt").write_text("requests>=2\nflask\n# c\n-r extra.txt\n")
    (tmp_path / "extra.txt").write_text("numpy\nrequests\n")
    names = [r.name for r in RequirementsTxtParser().parse(tmp_path / "reqs.txt")]
    assert names == ["requests", "flask", "numpy"]


def test_pyproject_pep621(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text('[project]\ndependencies = ["requests>=2", "Django[argon2]"]\n')
    assert sorted(r.name for r in PyprojectParser().parse(path)) == ["django", "requests"]


def test_pyproject_poetry_fallback(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(
        "[tool.poetry.dependencies]\n"
        'python = "^3.11"\n'
        'requests = "^2.0"\n'
        'Django = { version = "^4.0" }\n'
    )
    assert sorted(r.name for r in PyprojectParser().parse(path)) == ["django", "requests"]


def test_reader_prefers_configured_order(tmp_path):
    (tmp_path / "requirements.txt").write_text("flask\n")
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["django"]\n')
    reader = default_reader(["pyproject.toml", "requirements.txt"])
    result = reader.read(tmp_path)
    assert result.source.name == "pyproject.toml"
    assert result.names == frozenset({"django"})


def test_reader_returns_none_when_no_files(tmp_path):
    assert default_reader(["pyproject.toml"]).read(tmp_path) is None
