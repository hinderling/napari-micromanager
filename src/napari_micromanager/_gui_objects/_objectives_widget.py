"""Objective selector built on the non-deprecated PropertyWidget.

The upstream ``ObjectivesWidget`` in ``pymmcore_widgets.control._objective_widget``
wraps the deprecated ``StateDeviceWidget``, whose ``__init__`` writes the
current state back to the device on construction. On Nikon TI scopes that
re-applies the turret state: Z drops, PFS disables, the turret "rotates"
to its current position, Z raises. Hardware moves before the user touches
anything.

``PropertyWidget`` connects its valueChanged-to-core handler *after* the
initial setValue, so the same UI built on top of it has no startup write.

This local widget exists to keep the napari-mm testing branch
self-contained — once pymmcore-widgets PR #557 (the ``signals_blocked``
fix in ``StateDeviceWidget.__init__``) merges, this file can be removed
and ``_toolbar.py`` can go back to importing ``ObjectivesWidget`` from
``pymmcore_widgets``.
"""
from __future__ import annotations

from pymmcore_plus import CMMCorePlus
from pymmcore_widgets import PropertyWidget
from pymmcore_widgets._util import guess_objective_or_prompt
from qtpy.QtCore import Slot
from qtpy.QtWidgets import QComboBox, QHBoxLayout, QLabel, QSizePolicy, QWidget


class ObjectivesWidget(QWidget):
    """Drop-in replacement for ``pymmcore_widgets.ObjectivesWidget``."""

    def __init__(
        self,
        objective_device: str | None = None,
        *,
        parent: QWidget | None = None,
        mmcore: CMMCorePlus | None = None,
    ) -> None:
        super().__init__(parent=parent)
        self._mmc = mmcore or CMMCorePlus.instance()
        self._objective_device = objective_device or guess_objective_or_prompt(
            self._mmc, parent=self
        )

        lbl = QLabel("Objectives:")
        lbl.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)

        self._inner: QWidget = self._create_inner_widget()

        self.setLayout(QHBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().addWidget(lbl)
        self.layout().addWidget(self._inner)

        self._mmc.events.systemConfigurationLoaded.connect(self._on_sys_cfg_loaded)
        self.destroyed.connect(self._disconnect)

    def _create_inner_widget(self) -> QWidget:
        if self._objective_device and self._objective_device in self._mmc.getLoadedDevices():
            wdg = PropertyWidget(
                self._objective_device, "Label", parent=self, mmcore=self._mmc
            )
            wdg.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            wdg.valueChanged.connect(self._on_obj_changed)
            self.setMinimumWidth(0)
            wdg.adjustSize()
            return wdg
        placeholder = QComboBox(parent=self)
        placeholder.setEnabled(False)
        return placeholder

    @Slot()
    def _on_sys_cfg_loaded(self) -> None:
        loaded = self._mmc.getLoadedDevices()
        if self._objective_device not in loaded:
            self._objective_device = guess_objective_or_prompt(
                self._mmc, parent=self
            )
        self._inner.setParent(QWidget())
        self._inner = self._create_inner_widget()
        self.layout().addWidget(self._inner)

    @Slot(object)
    def _on_obj_changed(self, _value: object = None) -> None:
        self._mmc.events.pixelSizeChanged.emit(self._mmc.getPixelSizeUm() or 0.0)

    def _disconnect(self) -> None:
        try:
            self._mmc.events.systemConfigurationLoaded.disconnect(
                self._on_sys_cfg_loaded
            )
        except (TypeError, RuntimeError):
            pass
