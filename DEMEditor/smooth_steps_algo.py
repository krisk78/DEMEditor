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
from .dem_utils import meters_to_pixels
#from .dem_debug import *

from qgis.core import (
    Qgis,
    QgsProcessingAlgorithm,
    QgsProcessingContext,
    QgsProcessingException, # pyright: ignore[reportAttributeAccessIssue]
    QgsProcessingParameterBoolean,
    QgsProcessingParameterRasterLayer,
    QgsProcessingParameterRasterDestination,
    QgsProcessingParameterEnum,
    QgsProcessingParameterNumber,
    QgsRasterLayer
)

from qgis.PyQt.QtCore import QCoreApplication

from enum import Enum
import numpy as np


class TransitionType(Enum):
    LINEAR = 0
    QUADRATIC = 1
    CUBIC = 2
    COSINE = 3
    SMOOTHSTEP = 4


class EdgePriority(Enum):
    LOWER_ELEVATION = 0
    HIGHER_ELEVATION = 1


@dataclass
class FrontPoint:
    row: int
    col: int
    normal: tuple[float, float]
    z_ref: float


class SmoothStepsAlgorithm(QgsProcessingAlgorithm):

    INPUT = "INPUT"
    THRESHOLD = "THRESHOLD"
    RADIUS = "RADIUS"
    ANGLE = "ANGLE"
    PRIORITY = "PRIORITY"
    INTERPOL = "INTERPOL"
    MIN_ELEVATION = "MIN_ELEVATION"
    MAX_ELEVATION = "MAX_ELEVATION"
    OUTPUT = "OUTPUT"
    _DEMEDITOR = "_DEMEDITOR"

    def __init__(self):
        super().__init__()


    def name(self):
        return "smoothsteps"


    def displayName(self):
        return self.tr("Smooth Steps")


    def group(self):
        return self.tr("DEM Editor")


    def groupId(self):
        return "dem_editor"


    def tr(self, string):
        return QCoreApplication.translate(
            "SmoothStepsAlgorithm",
            string
        )


    def createInstance(self):
        return SmoothStepsAlgorithm()


    def initAlgorithm(self, configuration=None):

        self.addParameter(
            QgsProcessingParameterRasterLayer(
                self.INPUT,
                self.tr("Input DEM")
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.THRESHOLD,
                self.tr("Step threshold"),
                QgsProcessingParameterNumber.Double, # pyright: ignore[reportAttributeAccessIssue]
                defaultValue=0,
                minValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.RADIUS,
                self.tr("Smooth radius (meters)"),
                QgsProcessingParameterNumber.Double, # pyright: ignore[reportAttributeAccessIssue]
                defaultValue=15.0,
                minValue=0.0
            )
        )

        self.addParameter(
            QgsProcessingParameterNumber(
                self.ANGLE,
                self.tr("Smooth angle (degrees)"),
                QgsProcessingParameterNumber.Double, # pyright: ignore[reportAttributeAccessIssue]
                defaultValue=15.0,
                minValue=0
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.INTERPOL,
                self.tr("Interpolation"),
                options=[
                    self.tr("Linear"),
                    self.tr("Quadratic"),
                    self.tr("Cubic"),
                    self.tr("Cosine"),
                    self.tr("SmoothStep")
                ],
                defaultValue=3
            )
        )

        self.addParameter(
            QgsProcessingParameterEnum(
                self.PRIORITY,
                self.tr("Edge priority"),
                options=[
                    self.tr("Lower elevations"),
                    self.tr("Higher elevations"),
                ],
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
        threshold = self.parameterAsDouble(parameters, self.THRESHOLD, context)
        radius = self.parameterAsDouble(parameters, self.RADIUS, context)
        angle = self.parameterAsDouble(parameters, self.ANGLE, context)
        interpol = self.parameterAsInt(parameters, self.INTERPOL, context)
        priority = self.parameterAsInt(parameters, self.PRIORITY, context)
        min_elevation = self.parameterAsDouble(parameters, self.MIN_ELEVATION, context)
        max_elevation = self.parameterAsDouble(parameters, self.MAX_ELEVATION, context)
        output = self.parameterAsOutputLayer(parameters, self.OUTPUT, context)
        _dem_editor = self.parameterAsBoolean(parameters, self._DEMEDITOR, context)

        if input_layer is None:
            raise QgsProcessingException(self.tr("Invalid input raster"))

        transition_radius = meters_to_pixels(input_layer, radius)
        transition_type = TransitionType(interpol)
        edge_priority = EdgePriority(priority)

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

        front_pixels = detect_front_pixels(
            array=raster_data.array,
            layer=input_layer,
            threshold=threshold,
            edge_priority=edge_priority,
            pixel_filter=combined_filter
        )

        if len(front_pixels) == 0:
            raise QgsProcessingException(
                "No front point matching conditions has been detected."
                " Processing cancelled."
                " Review polygon selection and/or processing parameters.")

        front_directions = compute_front_directions(
            array=raster_data.array,
            front_pixels=front_pixels,
            edge_priority=edge_priority,
            threshold=threshold
        )

        smooth_front_transitions(
            array=raster_data.array,
            front_points=front_directions,
            transition_radius=transition_radius,
            transition_angle=angle,
            transition_type=transition_type,
            edge_priority=edge_priority
        )

        save_geotiff(
            arr=raster_data.array,
            path=output,
            crs=input_layer.crs(),
            geo_transform=raster_data.geo_transform,
            nodata=raster_data.nodata
        )

        return {
            self.INPUT: input_layer,
            self.OUTPUT: output
        }


def detect_front_pixels(
        array: np.ndarray,
        layer: QgsRasterLayer,
        threshold: float,
        edge_priority: EdgePriority,
        pixel_filter: PixelFilter
) -> list[tuple[int, int]]:

    front_pixels = []
    height, width = array.shape

    candidate_windows = pixel_filter.candidate_windows(layer)
    if candidate_windows is None:
        raise ValueError("Unable to get candidates from geometries")

    for row_min, row_max, col_min, col_max in candidate_windows:

        # avoid raster limits
        row_min = max(row_min, 1)
        col_min = max(col_min, 1)
        row_max = min(row_max, height - 2)
        col_max = min(col_max, width - 2)

        for row in range(row_min, row_max + 1):
            for col in range(col_min, col_max + 1):

                z = array[row, col]

                if not pixel_filter.accept(row, col, z):
                    continue

                neighbors = [
                    array[row - 1, col],
                    array[row + 1, col],
                    array[row, col - 1],
                    array[row, col + 1]
                ]

                if edge_priority is EdgePriority.LOWER_ELEVATION:
                    # searching a high pixel with a low pixel neighbor
                    if any(z - zn >= threshold for zn in neighbors):
                        front_pixels.append((row, col))

                elif edge_priority is EdgePriority.HIGHER_ELEVATION:
                    # searching a low pixel with a high pixel neighbor
                    if any(zn - z >= threshold for zn in neighbors):
                        front_pixels.append((row, col))

    return front_pixels


def compute_front_directions(
        array: np.ndarray,
        front_pixels: list[tuple[int, int]],
        edge_priority: EdgePriority,
        threshold: float
) -> list[FrontPoint]:

    results = []

    neighbors = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]

    for row, col in front_pixels:

        # find neighbors that matches the threshold condition
        ref_candidates = []
        z_front = array[row, col]
        for dy, dx in neighbors:
            z = array[row + dy, col + dx]
            delta_z = z - z_front
            if(
                edge_priority is EdgePriority.LOWER_ELEVATION and delta_z <= -threshold
                or edge_priority is EdgePriority.HIGHER_ELEVATION and delta_z >= threshold

            ):
                ref_candidates.append((dy, dx, z))
        if len(ref_candidates) == 8:
            # cannot determine the normal in this context
            continue

        # remove inconsistent points
        mean_dy = np.mean([c[0] for c in ref_candidates])
        mean_dx = np.mean([c[1] for c in ref_candidates])

        filtered_candidates = [
            (dy, dx, z)
            for dy, dx, z in ref_candidates
            if dy * mean_dy + dx * mean_dx >= 0
        ]

        assert filtered_candidates

        # calculate the normal
        mean_dy = np.mean([c[0] for c in filtered_candidates])
        mean_dx = np.mean([c[1] for c in filtered_candidates])

        norm = np.hypot(mean_dx, mean_dy)
        if norm == 0:
            # unable to calculate a reliable normal
            continue
        ny = -mean_dy / norm
        nx = -mean_dx / norm

        # reference elevation to apply at the beginnig of the transition
        z_ref = np.median([c[2] for c in filtered_candidates])

        # save for transition application
        results.append(
            FrontPoint(
                row=row,
                col=col,
                normal=(ny, nx),
                z_ref=z_ref
            )
        )

    return results


def smooth_front_transitions(
        array: np.ndarray,
        front_points: list[FrontPoint],
        transition_radius: int,
        transition_angle:float,
        transition_type: TransitionType,
        edge_priority: EdgePriority
):

    source_array = array.copy()
    half_angle = np.deg2rad(transition_angle / 2.0)

    for fp in front_points:

        ny, nx = fp.normal

        # tangent vector
        ty = -nx
        tx = ny

        for distance in range(1, transition_radius + 1):

            # sector opening
            width = int(round((distance - 1) * np.tan(half_angle)))

            for s in range(-width, width + 1):

                row = int(round(fp.row + (distance - 1) * ny + s * ty))
                col = int(round(fp.col + (distance - 1) * nx + s * tx))
                row = np.clip(row, 0, array.shape[0]-1)
                col = np.clip(col, 0, array.shape[1]-1)

                # radius direction
                vy = distance * ny + s * ty
                vx = distance * nx + s * tx
                norm = np.hypot(vx, vy)
                if norm == 0:
                    continue
                vy /= norm
                vx /= norm
                dot = ny * vy + nx * vx
                angular_weight = dot * dot

                # z_target at the radius
                target_row = int(round(fp.row + transition_radius * vy))
                target_col = int(round(fp.col + transition_radius * vx))
                target_row = np.clip(target_row, 0, array.shape[0]-1)
                target_col = np.clip(target_col, 0, array.shape[1]-1)
                z_target = source_array[target_row, target_col]

                # transition factor
                t = distance / transition_radius
                factor = transition_factor(t, transition_type)
                factor *= angular_weight

                # new z calculation
                z_source = source_array[row, col]
                z_transition = fp.z_ref + factor * (z_target - fp.z_ref)
                z = z_source + (z_transition - z_source)

                if edge_priority is EdgePriority.LOWER_ELEVATION:
                    array[row, col] = min(array[row, col], z)
                else:
                    array[row, col] = max(array[row, col], z)


def create_circle_mask(radius: int) -> np.ndarray:

    size = radius * 2 + 1
    circle_mask = np.zeros((size, size), dtype=bool)

    cy = cx = radius
    r2 = radius * radius

    for y in range(size):
        for x in range(size):
            d2 = (y - cy) ** 2 + (x - cx) ** 2

            # get a thin circle
            if abs(d2 - r2) <= radius:
                circle_mask[y, x] = True

    return circle_mask


def find_masks_intersections(
        bool_mask: np.ndarray,
        row: int,
        col: int,
        search_mask: np.ndarray,
        offset_y: int,
        offset_x: int
) -> np.ndarray:

    size_y = search_mask.shape[0]
    size_x = search_mask.shape[1]

    local_lines = bool_mask[
        row+offset_y:row+offset_y+size_y,
        col+offset_x:col+offset_x+size_x
    ]

    intersections = local_lines & search_mask

    points = np.argwhere(intersections)

    points[:, 0] += row + offset_y 
    points[:, 1] += col + offset_x

    return points


def transition_factor(t: float, transition_type: TransitionType) -> float:

    if transition_type is TransitionType.LINEAR:
        return t

    if transition_type is TransitionType.QUADRATIC:
        return t * t

    if transition_type is TransitionType.CUBIC:
        return t ** 3

    if transition_type is TransitionType.COSINE:
        return (1 - np.cos(np.pi * t)) / 2

    if transition_type is TransitionType.SMOOTHSTEP:
        return t * t * (3 - 2 * t)
    