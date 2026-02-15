"""Run napari-micromanager as a script with ``python -m napari_micromanager``."""

from __future__ import annotations

import argparse
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


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
    parser.add_argument(
        "-r",
        "--remote",
        type=str,
        default=None,
        help="Connect to a pymmcore-proxy server (e.g. http://microscope:5600)",
    )
    parsed_args = parser.parse_args(args)

    import napari

    from napari_micromanager.main_window import MainWindow

    viewer = napari.Viewer()

    if parsed_args.remote:
        import pymmcore_plus.core._mmcore_plus as _core_mod

        from pymmcore_proxy import RemoteMMCore
        from qtpy.QtCore import QObject, Signal as QtSignal, Slot

        # Create core without starting signal listener yet — we need the
        # QApplication (created by napari.Viewer above) before setting up
        # the Qt relay.
        remote_core = RemoteMMCore(parsed_args.remote, connect_signals=False)

        # Relay signal dispatches from the WebSocket thread to the Qt main
        # thread.  Without this, callbacks triggered by psygnal signals
        # (widget updates, timers, layer creation) would run on the WS
        # thread and crash Qt.
        class _MainThreadRelay(QObject):
            _sig = QtSignal(object)

            def __init__(self, dispatch_fn: object) -> None:
                super().__init__()
                self._fn = dispatch_fn
                self._sig.connect(self._handle)

            @Slot(object)
            def _handle(self, msg: object) -> None:
                self._fn(msg)

        _relay = _MainThreadRelay(remote_core._dispatch_signal)
        remote_core._dispatch_signal = _relay._sig.emit
        remote_core._relay = _relay  # prevent garbage collection

        remote_core._start_signal_listener()
        _core_mod._instance = remote_core
        config = None
    else:
        config = parsed_args.config

    win = MainWindow(viewer, config=config)
    dw = viewer.window.add_dock_widget(win, name="MicroManager", area="top")
    if hasattr(dw, "_close_btn"):
        dw._close_btn = False
    napari.run()


if __name__ == "__main__":
    main()
