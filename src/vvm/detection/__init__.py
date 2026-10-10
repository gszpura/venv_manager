"""Virtual environment detection."""

from vvm.detection.detector import VenvDetector, python_version
from vvm.detection.factory import build_detector
from vvm.detection.format import (
    TableVenvFormatter,
    TextVenvFormatter,
    VenvFormatter,
    supports_color,
)
from vvm.detection.locator import (
    ConfiguredDirStrategy,
    CurrentDirStrategy,
    LocationStrategy,
    VenvLocator,
)

__all__ = [
    "ConfiguredDirStrategy",
    "CurrentDirStrategy",
    "LocationStrategy",
    "TableVenvFormatter",
    "TextVenvFormatter",
    "VenvDetector",
    "VenvFormatter",
    "VenvLocator",
    "build_detector",
    "python_version",
    "supports_color",
]
