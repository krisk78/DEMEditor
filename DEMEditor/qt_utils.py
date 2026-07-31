# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from processing.gui.ParametersPanel import ParametersPanel
from qgis.gui import QgsAbstractProcessingParameterWidgetWrapper, QgisInterface
from qgis.PyQt.QtWidgets import QMessageBox, QWidget, QProgressBar, QMainWindow
from qgis.utils import iface

import processing
from typing import cast



def get_parameter_wrapper(
    dialog: processing.AlgorithmDialog,
    name: str
) -> QgsAbstractProcessingParameterWidgetWrapper|None:
    
    panels = dialog.findChildren(ParametersPanel)
    if not panels:
        return None
    return panels[0].wrappers.get(name)


def set_parameter_enabled(
        dialog: processing.AlgorithmDialog,
        name: str,
        enabled: bool
):
    
    wrapper = get_parameter_wrapper(dialog, name)
    if wrapper is None:
        return
    
    widget = wrapper.wrappedWidget()
    if widget:
        widget.setEnabled(enabled)
    
    label = wrapper.wrappedLabel()
    if label:
        label.setEnabled(enabled)


def display_important_warning(
        parent_widget: QWidget,
        title: str,
        text: str,
        information: str,
        confirm: str,
        cancel: str
) -> bool:

    msg = QMessageBox(parent_widget)
    msg.setIcon(QMessageBox.Warning)
    msg.setWindowTitle(title)
    msg.setText(text)
    msg.setInformativeText(information)

    confirm_btn = msg.addButton(confirm, QMessageBox.DestructiveRole)
    cancel_btn = msg.addButton(cancel, QMessageBox.RejectRole)

    msg.setDefaultButton(cancel_btn)
    msg.exec()

    return msg.clickedButton() is confirm_btn


class StatusProgress:

    def __init__(self, message: str, progress: int):
        
        qgis_iface = cast(QgisInterface, iface)
        window = qgis_iface.mainWindow()
        main_window = cast(QMainWindow, window)
        self.status_bar = main_window.statusBar()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.update(message, progress)


    def update(self, message: str, progress: int):

        self.progress_bar.setValue(progress)
        self.status_bar.showMessage(message)


    def close(self):

        self.status_bar.removeWidget(self.progress_bar)
        self.status_bar.clearMessage()
        self.progress_bar.deleteLater()
