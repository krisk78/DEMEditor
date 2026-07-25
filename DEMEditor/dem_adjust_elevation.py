from .edit_context import DEMEditContext
from .adjust_elevation_algo import AdjustElevationAlgorithm
from .pixel_filter import PolygonFilter
from .qt_utils import set_parameter_enabled
from . import adjust_elevation_context

from typing import cast

import processing


class DEMAdjustElevation:

    def run(self, context: DEMEditContext):

        alg = AdjustElevationAlgorithm()

        parameters = {
            AdjustElevationAlgorithm.INPUT: context.input_layer,
            AdjustElevationAlgorithm.OUTPUT: "TEMPORARY_OUTPUT",
            AdjustElevationAlgorithm._DEMEDITOR: True
        }

        dlg = processing.createAlgorithmDialog(alg, parameters)
        assert dlg is not None
        dlg =cast(processing.AlgorithmDialog, dlg)
        alg = cast(AdjustElevationAlgorithm, dlg.algorithm())

        if context.input_layer is not None:
            set_parameter_enabled(dlg, "INPUT", False)
        set_parameter_enabled(dlg, "OUTPUT", False)

        adjust_elevation_context._filter = PolygonFilter(context.geometries)
        result = dlg.exec()

        return adjust_elevation_context._output_layer
    