# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from .edit_context import DEMEditContext
from .pixel_filter import PolygonFilter
from .qt_utils import set_parameter_enabled
from . import algorithm_context
from .external_algo import ExternalAlgorithm
from .raster_calculator import RasterCalculatorAlgorithm
from .user_expression import UserExpressionAlgorithm
from .dem_utils import get_project_layer_from_source

from qgis.core import QgsProcessingAlgorithm
import processing

from typing import Type, cast


class DEMAlgorithmWrapper:

    def run(self, algorithm_cls: Type[QgsProcessingAlgorithm], context: DEMEditContext):

        alg = algorithm_cls()

        parameters = {
            algorithm_cls.INPUT: context.input_layer, # pyright: ignore[reportAttributeAccessIssue]
            algorithm_cls.OUTPUT: "TEMPORARY_OUTPUT", # pyright: ignore[reportAttributeAccessIssue]
            algorithm_cls._DEMEDITOR: True # pyright: ignore[reportAttributeAccessIssue]
        }

        dlg = processing.createAlgorithmDialog(alg, parameters)
        assert dlg is not None
        dlg = cast(processing.AlgorithmDialog, dlg)

        if context.input_layer is not None:
            set_parameter_enabled(dlg, "INPUT", False)
        set_parameter_enabled(dlg, "OUTPUT", False)

        algorithm_context._filter = PolygonFilter(context.geometries)
        result = dlg.exec()

        if not dlg.results():
            return None

        # get the source layer renderer
        renderer = None
        input_raster = dlg.results().get("INPUT")
        if input_raster is not None:
            renderer = input_raster.renderer().clone()

        if context.wrapper_algo:
            alg = dlg.algorithm()
            assert alg is not None
            if algorithm_cls is ExternalAlgorithm:
                alg = cast(ExternalAlgorithm, alg)
            elif algorithm_cls is RasterCalculatorAlgorithm:
                alg = cast(RasterCalculatorAlgorithm, alg)
            elif algorithm_cls is UserExpressionAlgorithm:
                alg = cast(UserExpressionAlgorithm, alg)
            else:
                raise NotImplementedError
            output = alg.post_processing(dlg.results())

        else:
            output = dlg.results().get("OUTPUT")

        if output is None:
            return None
        
        output_layer = get_project_layer_from_source(output)
        if output_layer is not None and renderer is not None:
            # set same renderer as source layer
            output_layer.setRenderer(renderer)
            output_layer.triggerRepaint()

        return output_layer
    