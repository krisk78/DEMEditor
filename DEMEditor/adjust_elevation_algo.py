from .pixel_filter import *
from .io import *
from . import algorithm_context

from qgis.core import (
    Qgis,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException,
    QgsProcessingParameterBoolean,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsRasterLayer
)

from qgis.PyQt.QtCore import QCoreApplication

import numpy as np


class AdjustElevationAlgorithm(QgsProcessingAlgorithm):

    INPUT = "INPUT"
    MODE = "MODE"
    VALUE = "VALUE"
    MIN_ELEVATION = "MIN_ELEVATION"
    MAX_ELEVATION = "MAX_ELEVATION"
    OUTPUT = "OUTPUT"
    _DEMEDITOR = "_DEMEDITOR"


    def __init__(self):

        super().__init__()


    def name(self):
        return "adjustelevation"


    def displayName(self):
        return self.tr("Adjust elevation")


    def group(self):
        return self.tr("DEM Editor")


    def groupId(self):
        return "dem_editor"


    def tr(self, string):

        return QCoreApplication.translate(
            "AdjustElevationAlgorithm",
            string
        )


    def createInstance(self):
        return AdjustElevationAlgorithm()


    def initAlgorithm(self, configuration=None):

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr("Input DEM")
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.MODE,
                self.tr("Adjustment mode"),
                options=[
                    self.tr("Relative offset"),
                    self.tr("Absolute elevation"),
                ],
                defaultValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.VALUE,
                self.tr("Elevation value"),
                QgsProcessingParameterNumber.Double, # pyright: ignore[reportAttributeAccessIssue]
                defaultValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MIN_ELEVATION,
                self.tr("Minimum elevation"),
                QgsProcessingParameterNumber.Double, # pyright: ignore[reportAttributeAccessIssue]
                defaultValue=-99999
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.MAX_ELEVATION,
                self.tr("Maximum elevation"),
                QgsProcessingParameterNumber.Double, # pyright: ignore[reportAttributeAccessIssue]
                defaultValue=99999
            )
        )

        self.addParameter(
            QgsProcessingParameterRasterDestination(
                self.OUTPUT,
                self.tr("Output DEM")
            )
        )

        param = QgsProcessingParameterBoolean(
            self._DEMEDITOR,
            defaultValue=False
        )
        param.setFlags(
            param.flags() | Qgis.ProcessingParameterFlag.Hidden # pyright: ignore[reportAttributeAccessIssue]
        )
        self.addParameter(param)


    def processAlgorithm(self, parameters, context: QgsProcessingContext, feedback):

        input_layer = self.parameterAsRasterLayer(parameters, self.INPUT, context)
        mode = self.parameterAsInt(parameters, self.MODE, context)
        value = self.parameterAsDouble(parameters, self.VALUE, context)
        min_elevation = self.parameterAsDouble(parameters, self.MIN_ELEVATION, context)
        max_elevation = self.parameterAsDouble(parameters, self.MAX_ELEVATION, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        _dem_editor = self.parameterAsBoolean(parameters, self._DEMEDITOR, context)

        if input_layer is None:
            raise QgsProcessingException(self.tr("Invalid input raster"))
        
        filter: PixelFilter|None = None
        if _dem_editor:
            filter = algorithm_context._filter
        if filter is None:
            filter = FullRasterFilter()
        
        raster_data = read_raster_layer(input_layer)

        combined_filter = AndFilter(
            filter,
            ElevationFilter(
                min_elevation=min_elevation,
                max_elevation=max_elevation
            )
        )

        self.apply_adjustment(
            array=raster_data.array,
            layer=input_layer,
            mode=mode,
            value=value,
            filter=combined_filter
        )

        save_geotiff(
            arr=raster_data.array,
            path=output,
            crs=input_layer.crs(),
            geo_transform=raster_data.geo_transform,
            nodata=raster_data.nodata
        )

        return {
            self.OUTPUT: output
        }
    

    def apply_adjustment(
        self,
        array: np.ndarray,
        layer: QgsRasterLayer,
        mode: int,
        value: float,
        filter: PixelFilter
    ):

        candidate_windows = filter.candidate_windows(layer)
        if candidate_windows is None:
            raise ValueError("Unable to get candidates from geometries")

        for window in candidate_windows:

            for row in range(window[0], window[1] + 1):

                for col in range(window[2], window[3] + 1):

                    if filter.accept(row, col, array[row, col]):

                        if mode == 0:  # relative
                            array[row, col] += value
                        else:  # absolute
                            array[row, col] = value
