
from vvm.inspection import (
    DefaultCategoryClassifier,
    find_python,
    find_site_packages,
    is_venv,
    read_pyvenv_cfg,
)
from vvm.models import VenvCategory


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


def test_default_classifier(make_venv):
    venv = make_venv("env")
    assert DefaultCategoryClassifier().classify(venv, frozenset()) == (VenvCategory.UNKNOWN,)
