"""Run napari-micromanager as a script with ``python -m napari_micromanager``."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def _has_py_devices(cfg_path: str) -> bool:
    """Return True if the .cfg file contains #py pyDevice lines."""
    try:
        with open(cfg_path) as f:
            return any(
                line.strip().startswith("#py pyDevice")
                for line in f
            )
    except OSError:
        return False


def main(args: Sequence[str] | None = None) -> None:
    """Create a napari viewer and add the MicroManager plugin to it."""
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(description="Enter string")
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        default=None,
        help="Config file to load",
        nargs="?",
    )
    parsed_args = parser.parse_args(args)

    import napari

    from napari_micromanager.main_window import MainWindow

    viewer = napari.Viewer()

    config = parsed_args.config
    if config is not None and _has_py_devices(config):
        from pymmcore_plus.experimental.unicore import UniMMCore
        import pymmcore_plus.core._mmcore_plus as _core_mod
        _core_mod._instance = UniMMCore()

    win = MainWindow(viewer, config=config)
    dw = viewer.window.add_dock_widget(win, name="MicroManager", area="top")
    if hasattr(dw, "_close_btn"):
        dw._close_btn = False
    napari.run()


if __name__ == "__main__":
    main()
