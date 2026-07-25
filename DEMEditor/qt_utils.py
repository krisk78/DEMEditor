from processing.gui.ParametersPanel import ParametersPanel
from qgis.gui import QgsAbstractProcessingParameterWidgetWrapper

import processing


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
