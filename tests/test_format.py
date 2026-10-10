from pathlib import Path

from vvm.detection.format import (
    TableVenvFormatter,
    TextVenvFormatter,
    colorize,
    supports_color,
)
from vvm.models import Venv

VENVS = [
    Venv(path=Path("/v/ai"), packages=frozenset({"torch"}), categories=("ai",)),
    Venv(path=Path("/v/api"), packages=frozenset({"flask", "requests"}), categories=("server",)),
]


def test_text_formatter_one_line_per_venv():
    out = TextVenvFormatter().render(VENVS)
    assert "/v/ai [ai] 1 packages" in out
    assert "/v/api [server] 2 packages" in out


def test_table_formatter_columns_and_solid_box():
    out = TableVenvFormatter(color=False).render(VENVS)
    assert "Path" in out
    assert "Category" in out
    assert "Packages" in out
    assert "/v/ai" in out and "ai" in out and "/v/api" in out
    assert "─" in out  # solid horizontal box-drawing line
    assert "╭" in out and "╰" in out  # rounded solid corners


def test_table_formatter_colors_when_enabled():
    assert "\x1b[" not in TableVenvFormatter(color=False).render(VENVS)
    assert "\x1b[" in TableVenvFormatter(color=True).render(VENVS)


def test_colorize():
    assert colorize("x", "\x1b[31m", True) == "\x1b[31mx\x1b[0m"
    assert colorize("x", "\x1b[31m", False) == "x"


class _Tty:
    def isatty(self) -> bool:
        return True


class _NotTty:
    def isatty(self) -> bool:
        return False


def test_supports_color(monkeypatch):
    monkeypatch.delenv("NO_COLOR", raising=False)
    monkeypatch.delenv("FORCE_COLOR", raising=False)
    assert supports_color(_Tty()) is True
    assert supports_color(_NotTty()) is False

    monkeypatch.setenv("NO_COLOR", "1")
    assert supports_color(_Tty()) is False

    monkeypatch.delenv("NO_COLOR")
    monkeypatch.setenv("FORCE_COLOR", "1")
    assert supports_color(_NotTty()) is True
