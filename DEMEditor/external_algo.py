# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from .pixel_filter import *
from .io import *
from . import algorithm_context
from .qt_utils import set_parameter_enabled
from .dem_utils import add_project_layer_from_source, remove_project_layer_by_source

from qgis.core import (
    Qgis,
    QgsProcessingAlgorithm, 
    QgsProcessingContext, 
    QgsProcessingException, # pyright: ignore[reportAttributeAccessIssue]
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterBoolean,
    QgsProcessingUtils
)
from qgis.PyQt.QtCore import QCoreApplication
import processing

from enum import Enum
from typing import Any, cast


class Algorithm(Enum):
    GRASS_NEIGHBORS = "grass:r.neighbors"


class SelectionMode(Enum):
    RASTER = "raster"
    EXTENT = "extent"


@dataclass
class Extent:
    y_min: int
    y_max: int
    x_min: int
    x_max: int


@dataclass
class Margins:
    left: int
    right: int
    top: int
    bottom: int


@dataclass
class AlgorithmFeatures:
    description: str
    selection_mode: SelectionMode
    input_parameter: str = "input"
    output_parameter:str = "output"
    selection_parameter: str|None = None


class ExternalAlgorithm(QgsProcessingAlgorithm):

    INPUT = "INPUT"
    EXT_ALGO = "EXT_ALGO"
    BUFF_AREA = "BUFF_AREA"
    MIN_ELEVATION = "MIN_ELEVATION"
    MAX_ELEVATION = "MAX_ELEVATION"
    OUTPUT = "OUTPUT"
    _DEMEDITOR = "_DEMEDITOR"

    ALGO_LIST = {
        Algorithm.GRASS_NEIGHBORS: AlgorithmFeatures(
            description="GRASS r.neighbors (set buffer area)",
            selection_mode=SelectionMode.EXTENT,
            #selection_parameter="selection"
        )
    }

    ALGO_KEYS = list(ALGO_LIST.keys())


    def __init__(self):

        super().__init__()


    def name(self):
        return "externalalgorithm"


    def displayName(self):
        return self.tr("External algorithm")


    def group(self):
        return self.tr("DEM Editor")


    def groupId(self):
        return "dem_editor"


    def tr(self, string):

        return QCoreApplication.translate(
            "ExternalAlgorithm",
            string
        )


    def createInstance(self):
        return ExternalAlgorithm()


    def initAlgorithm(self, configuration=None):

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr("Input DEM")
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.EXT_ALGO,
                self.tr("External algorithm"),
                options=[
                    self.tr(self.ALGO_LIST[key].description) for key in self.ALGO_KEYS
                ],
                defaultValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.BUFF_AREA,
                self.tr("Buffer area (cells)"),
                QgsProcessingParameterNumber.Integer, # pyright: ignore[reportAttributeAccessIssue]
                defaultValue=10,
                minValue=0
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
        algo = self.parameterAsInt(parameters, self.EXT_ALGO, context)
        buffer = self.parameterAsInt(parameters, self.BUFF_AREA, context)
        min_elevation = self.parameterAsDouble(parameters, self.MIN_ELEVATION, context)
        max_elevation = self.parameterAsDouble(parameters, self.MAX_ELEVATION, context)
        #output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        demeditor_context = self.parameterAsBoolean(parameters, self._DEMEDITOR, context)

        algo_key = self.ALGO_KEYS[algo]

        if feedback is not None:
            feedback.pushInfo(
                "Preparing parameters for external processing."
                "Close this window to run it."
            )

        return {
            "INPUT": input_layer,
            "ALGO": algo_key,
            "BUFFER": buffer,
            "MIN_ELEVATION": min_elevation,
            "MAX_ELEVATION": max_elevation,
            #"OUTPUT_PATH" : output,
            "_DEMEDITOR": demeditor_context
        }
    

    def post_processing(self, results: dict[str, Any]) -> str|None:

        input_layer = results.get("INPUT")
        algo_key = results.get("ALGO")
        buffer = results.get("BUFFER")
        min_elevation = results.get("MIN_ELEVATION")
        max_elevation = results.get("MAX_ELEVATION")
        #output_path = results.get("OUTPUT_PATH")
        demeditor_context = results.get("_DEMEDITOR")

        if input_layer is None:
            raise QgsProcessingException(self.tr("Invalid input raster"))

        if algo_key is None:
            raise QgsProcessingException(self.tr("Invalid algorithm"))

        # if output_path is None:
        #     raise QgsProcessingException(self.tr("Invalid output path"))

        if buffer is None:
            buffer = 0

        algo_features = self.ALGO_LIST[algo_key]

        filter: PixelFilter|None = None
        if demeditor_context:
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

        candidate_windows = combined_filter.candidate_windows(input_layer)
        if candidate_windows is None:
            raise ValueError("Unable to get candidates from geometries")

        selection_points = get_selection_points(
            array=raster_data.array,
            candidate_windows=candidate_windows,
            filter=combined_filter
        )

        output = None

        if algo_features.selection_mode is SelectionMode.RASTER:
            output = self.run_with_selection_raster(
                algo=algo_key,
                layer=input_layer,
                raster_data=raster_data,
                selection_points=selection_points
            )

        elif algo_features.selection_mode is SelectionMode.EXTENT:
            output = self.run_with_extent(
                algo=algo_key,
                raster_data=raster_data,
                layer=input_layer,
                selection_points=selection_points,
                buffer=buffer,
                #output_path=output_path
            )

        return output


    def run_with_selection_raster(
            self,
            algo: Algorithm,
            layer: QgsRasterLayer,
            raster_data: RasterData|None,
            selection_points: list[tuple[int, int]]
    ) -> str|None:

        # remove raster data from memory
        assert raster_data is not None
        raster_shape = raster_data.array.shape
        data_type = raster_data.array.dtype
        geo_transform = raster_data.geo_transform
        nodata_value = raster_data.nodata
        raster_data = None

        # build the selection layer
        selection_dtype = np.uint8
        selection_nodata = 0
        selection_array = np.full(
            raster_shape,
            selection_nodata,
            selection_dtype
        )

        for row, col in selection_points:
            selection_array[row, col] = 1

        temp_path = QgsProcessingUtils.generateTempFilename("selection.tif")

        save_geotiff(
            arr=selection_array,
            path=temp_path,
            crs=layer.crs(),
            geo_transform=geo_transform,
            nodata=selection_nodata
        )

        # prepare the dialog of the external algorithm
        features = self.ALGO_LIST[algo]
        parameters = {
            features.input_parameter: layer,
            features.selection_parameter: temp_path,
            features.output_parameter: "TEMPORARY_OUTPUT"
        }
        dlg = processing.createAlgorithmDialog(algo.value, parameters)
        assert dlg is not None
        dlg = cast(processing.AlgorithmDialog, dlg)

        set_parameter_enabled(dlg, features.input_parameter, False)
        set_parameter_enabled(dlg, features.output_parameter, False)
        assert features.selection_parameter is not None
        set_parameter_enabled(dlg, features.selection_parameter, False)

        # execute the external processing and return its result
        result = dlg.exec()
        output = dlg.results().get(features.output_parameter)
        return output


    def run_with_extent(
            self,
            algo: Algorithm,
            raster_data: RasterData,
            layer: QgsRasterLayer,
            selection_points: list[tuple[int, int]],
            buffer: int,
            #output_path: str
    ) -> str|None:

        # layer extent
        layer_extent = Extent(
            y_min = min(p[0] for p in selection_points),
            y_max = max(p[0] for p in selection_points),
            x_min = min(p[1] for p in selection_points),
            x_max = max(p[1] for p in selection_points) 
        )

        # free margins
        margins = Margins(
            left = layer_extent.x_min,
            right = raster_data.array.shape[1]-1 - layer_extent.x_max,
            top = layer_extent.y_min,
            bottom = raster_data.array.shape[0]-1 - layer_extent.y_max
        )

        # available buffers
        clipped_buffer = Margins(
            left = min(buffer, margins.left),
            right = min(buffer, margins.right),
            top = min(buffer, margins.top),
            bottom = min(buffer, margins.bottom)
        )

        # buffered extent
        buffered_extent = Extent(
            y_min = layer_extent.y_min - clipped_buffer.top,
            y_max = layer_extent.y_max + clipped_buffer.bottom,
            x_min = layer_extent.x_min - clipped_buffer.left,
            x_max = layer_extent.x_max + clipped_buffer.right
        )

        # build the clipped layer
        crop_array = raster_data.array[
            buffered_extent.y_min:buffered_extent.y_max+1,
            buffered_extent.x_min:buffered_extent.x_max+1
        ]
        crop_geotr = list(raster_data.geo_transform)
        crop_geotr[0] += buffered_extent.x_min * crop_geotr[1]
        crop_geotr[3] += buffered_extent.y_min * crop_geotr[5]
        temp_path = QgsProcessingUtils.generateTempFilename("subraster.tif")
        save_geotiff(
            arr=crop_array,
            path=temp_path,
            crs=layer.crs(),
            geo_transform=tuple(crop_geotr),
            nodata=raster_data.nodata
        )

        # prepare the dialog of the external processing
        features = self.ALGO_LIST[algo]
        parameters = {
            features.input_parameter: temp_path,
            features.output_parameter: "TEMPORARY_OUTPUT"
        }
        dlg = processing.createAlgorithmDialog(algo.value, parameters)
        assert dlg is not None
        dlg = cast(processing.AlgorithmDialog, dlg)

        set_parameter_enabled(dlg, features.input_parameter, False)
        set_parameter_enabled(dlg, features.output_parameter, False)

        # execute the external processing and get its result
        result = dlg.exec()
        crop_output = dlg.results().get(features.output_parameter)

        if crop_output is None:
            return crop_output

        # read the result
        new_layer = QgsRasterLayer(crop_output, "External Result")
        if not new_layer.isValid():
            raise QgsProcessingException(f"Unable to load {crop_output}")
        new_raster = read_raster_layer(new_layer)
        # remove clipped buffers
        height, width = new_raster.array.shape
        new_raster.array = new_raster.array[
            clipped_buffer.top:height-clipped_buffer.bottom,
            clipped_buffer.left:width-clipped_buffer.right
        ]
        assert new_raster.array.shape == (
            layer_extent.y_max - layer_extent.y_min + 1,
            layer_extent.x_max - layer_extent.x_min + 1
        )

        # remove the cropped layer from project
        remove_project_layer_by_source(crop_output)
        
        # inject result in original raster
        rows = np.array([p[0] for p in selection_points])
        cols = np.array([p[1] for p in selection_points])
        raster_data.array[rows, cols] = new_raster.array[
            rows - layer_extent.y_min,
            cols - layer_extent.x_min
        ]
        temp_path = QgsProcessingUtils.generateTempFilename("output.tif")
        save_geotiff(
            arr=raster_data.array,
            path=temp_path,
            crs=layer.crs(),
            geo_transform=raster_data.geo_transform,
            nodata=raster_data.nodata
        )

        # add new layer to project
        add_project_layer_from_source(temp_path, f"{algo.value} result")

        return temp_path


def get_selection_points(
        array: np.ndarray,
        candidate_windows: list[tuple[int, int, int, int]],
        filter: PixelFilter
) -> list[tuple[int, int]]:

    selection = []
    for row_min, row_max, col_min, col_max in candidate_windows:
        for row in range(row_min, row_max + 1):
            for col in range(col_min, col_max + 1):
                if filter.accept(row, col, array[row, col]):
                    selection.append((row, col))
    return selection
