from dataclasses import dataclass

from qgis.core import QgsRasterLayer, QgsGeometry


@dataclass
class DEMEditContext:

    input_layer: QgsRasterLayer | None
    geometries: list[QgsGeometry]