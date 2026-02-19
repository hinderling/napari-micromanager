from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import MagicMock

import pytest

if TYPE_CHECKING:
    from pytestqt.qtbot import QtBot


def test_has_py_devices_true(tmp_path: Path) -> None:
    """Returns True when the cfg contains #py pyDevice lines."""
    from napari_micromanager.__main__ import _has_py_devices

    cfg = tmp_path / "test.cfg"
    cfg.write_text("#py pyDevice,Camera,mymodule,MyCamera\n")
    assert _has_py_devices(str(cfg)) is True


def test_has_py_devices_false(tmp_path: Path) -> None:
    """Returns False for a standard cfg with no #py lines."""
    from napari_micromanager.__main__ import _has_py_devices

    cfg = tmp_path / "test.cfg"
    cfg.write_text("# Standard config\nDevice,Camera,DemoCamera,DCam\n")
    assert _has_py_devices(str(cfg)) is False


def test_has_py_devices_missing_file() -> None:
    """Returns False (no crash) when the file does not exist."""
    from napari_micromanager.__main__ import _has_py_devices

    assert _has_py_devices("/nonexistent/path.cfg") is False


def test_main_window_core_injection(qtbot: QtBot) -> None:
    """MainWindow accepts an injected core and uses it as the singleton."""
    from pymmcore_plus import CMMCorePlus
    from pymmcore_plus.experimental.unicore import UniMMCore

    from napari_micromanager.main_window import MainWindow

    uni = UniMMCore()
    viewer = MagicMock()
    win = MainWindow(viewer, core=uni)
    qtbot.addWidget(win)

    assert win._mmc is uni
    assert isinstance(CMMCorePlus.instance(), UniMMCore)

    win._cleanup()


def test_load_py_device_cfg(tmp_path: Path) -> None:
    """UniMMCore can load a cfg with #py pyDevice lines."""
    from pymmcore_plus.experimental.unicore import UniMMCore

    # Write a minimal shutter device that UniMMCore can import
    module_file = tmp_path / "minimal_devices.py"
    module_file.write_text(
        "from pymmcore_plus.experimental.unicore import ShutterDevice\n"
        "\n"
        "class MinimalShutter(ShutterDevice):\n"
        "    def __init__(self):\n"
        "        super().__init__()\n"
        "        self._open = False\n"
        "    def get_open(self) -> bool:\n"
        "        return self._open\n"
        "    def set_open(self, open: bool) -> None:\n"
        "        self._open = open\n"
    )

    cfg_file = tmp_path / "minimal.cfg"
    cfg_file.write_text(
        "#py pyDevice,Shutter,minimal_devices,MinimalShutter\n"
        "#py Property,Core,Shutter,Shutter\n"
        "#py Property,Core,Initialize,1\n"
    )

    sys.path.insert(0, str(tmp_path))
    try:
        core = UniMMCore()
        core.loadSystemConfiguration(str(cfg_file))
        assert "Shutter" in core.getLoadedDevices()
    finally:
        sys.path.remove(str(tmp_path))
