from .pixel_filter import *
from .io import *
from . import algorithm_context
from .dem_utils import meters_to_pixels, group_points

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

from enum import Enum, auto
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
    z_target: float


class SmoothStepsAlgorithm(QgsProcessingAlgorithm):

    INPUT = "INPUT"
    THRESHOLD = "THRESHOLD"
    RADIUS = "RADIUS"
    PRIORITY = "PRIORITY"
    INTERPOL = "INTERPOL"
    MIN_ELEVATION = "MIN_ELEVATION"
    MAX_ELEVATION = "MAX_ELEVATION"
    OUTPUT = "OUTPUT"
    _DEMEDITOR = "_DEMEDITOR"

    CIRCLE_RADIUS:int = 7


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
                QgsProcessingParameterNumber.Integer, # pyright: ignore[reportAttributeAccessIssue]
                defaultValue=15,
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
        radius = self.parameterAsInt(parameters, self.RADIUS, context)
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
        circle_radius = meters_to_pixels(input_layer, self.CIRCLE_RADIUS)

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

        front_mask = detect_front_pixels(
            array=raster_data.array,
            layer=input_layer,
            threshold=threshold,
            edge_priority=edge_priority,
            pixel_filter=combined_filter
        )

        front_directions = compute_front_directions(
            array=raster_data.array,
            front_mask=front_mask,
            transition_radius=transition_radius,
            circle_radius=circle_radius,
            edge_priority=edge_priority
        )

        smooth_front_transitions(
            array=raster_data.array,
            front_points=front_directions,
            transition_radius=transition_radius,
            transition_type=transition_type
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


def detect_front_pixels(
        array: np.ndarray,
        layer: QgsRasterLayer,
        threshold: float,
        edge_priority: EdgePriority,
        pixel_filter: PixelFilter
) -> np.ndarray:

    height, width = array.shape
    front_mask = np.zeros(array.shape, bool)

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
                        front_mask[row, col] = True

                elif edge_priority is EdgePriority.HIGHER_ELEVATION:
                    # searching a low pixel with a high pixel neighbor
                    if any(zn - z >= threshold for zn in neighbors):
                        front_mask[row, col] = True

    return front_mask


def compute_front_directions(
        array: np.ndarray,
        front_mask: np.ndarray,
        transition_radius: int,
        circle_radius: int,
        edge_priority: EdgePriority
) -> list[FrontPoint]:

    height, width = array.shape
    results = []
    circle_mask = create_circle_mask(circle_radius)

    front_pixels = np.argwhere(front_mask)

    for row, col in front_pixels:

        local_front = front_mask[
            row-circle_radius:row+circle_radius+1,
            col-circle_radius:col+circle_radius+1
        ]
        intersections = local_front & circle_mask

        points = np.argwhere(intersections)
        groups = group_points(points)
        assert groups and len(groups) <= 2
        inter_points = []
        for group in groups:
            p = np.mean(group, axis = 0)
            inter_points.append((float(p[0]), float(p[1])))
        if len(inter_points) == 1:
            inter_points.append((float(row), float(col)))

        dy = inter_points[1][0] - inter_points[0][0]
        dx = inter_points[1][1] - inter_points[0][1]

        ny = -dx
        nx = dy
        norm = np.hypot(nx, ny)
        if norm:
            nx /= norm
            ny /= norm

        # can cases exist that do not give the expected elevation?
        # to check and consider a fallback,
        # but it will need the threshold value to be able to check
        z_ref = array[int(round(row - ny)), int(round(col - nx))]

        z_front = array[row, col]
        delta_z = z_ref - z_front
        if (
            edge_priority is EdgePriority.LOWER_ELEVATION and delta_z > 0
            or edge_priority is EdgePriority.HIGHER_ELEVATION and delta_z < 0
        ):
                ny = -ny
                nx = -nx
                z_ref = array[int(round(row - ny)), int(round(col - nx))]
        delta_z = z_ref - z_front
        assert delta_z != 0
        assert (
            edge_priority is EdgePriority.LOWER_ELEVATION and delta_z < 0
            or edge_priority is EdgePriority.HIGHER_ELEVATION and delta_z > 0
        )

        z_target = array[
            int(round(row + transition_radius * ny)),
            int(round(col + transition_radius * nx))
        ]

        results.append(
            FrontPoint(
                row=row,
                col=col,
                normal=(ny, nx),
                z_ref=z_ref,
                z_target=z_target))

    return results


def smooth_front_transitions(
        array: np.ndarray,
        front_points: list[FrontPoint],
        transition_radius: int,
        transition_type: TransitionType
):

    processed = np.zeros(array.shape, bool)

    for fp in front_points:

        for i in range(transition_radius + 1):

            row = int(round(fp.row + i * fp.normal[0]))
            col = int(round(fp.col + i * fp.normal[1]))

            if processed[row, col]:
                continue

            t = i / transition_radius
            factor = transition_factor(t, transition_type)

            array[row, col] = (fp.z_ref + factor * (fp.z_target - fp.z_ref))
            processed[row, col] = True


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
    