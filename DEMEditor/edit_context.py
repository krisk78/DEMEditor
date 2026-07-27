# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from dataclasses import dataclass

from qgis.core import QgsRasterLayer, QgsGeometry


@dataclass
class DEMEditContext:

    input_layer: QgsRasterLayer | None
    geometries: list[QgsGeometry]