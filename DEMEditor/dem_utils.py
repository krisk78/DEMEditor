# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from qgis.core import QgsRasterLayer, QgsProject

import numpy as np
from collections import deque
from pathlib import Path


def meters_to_pixels(layer: QgsRasterLayer, distance: float) -> int:

    units_per_pixel_x = layer.rasterUnitsPerPixelX()
    units_per_pixel_y = layer.rasterUnitsPerPixelY()

    pixel_size = (units_per_pixel_x + units_per_pixel_y) / 2.0

    if pixel_size <= 0:
        raise ValueError("Invalid raster pixel size")

    pixels = int(np.ceil(distance / pixel_size))
    return max(1, pixels)


def group_points(points: np.ndarray) -> list[list[tuple[int, int]]]:

    remaining = {tuple(p) for p in points}
    groups = []
    neighbors = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1),
        (1, -1),  (1, 0),  (1, 1)
    ]

    while remaining:

        start = remaining.pop()
        group = [start]

        queue = deque([start])
        while queue:

            y, x = queue.popleft()

            for dy, dx in neighbors:
                candidate = (y + dy, x + dx)

                if candidate in remaining:
                    remaining.remove(candidate)
                    group.append(candidate)
                    queue.append(candidate)

        groups.append(group)

    return groups


def add_project_layer_from_source(
        source: str,
        name: str
) -> QgsRasterLayer|None:

    layer = QgsRasterLayer(source, name)

    if not layer.isValid():
        return None

    instance = QgsProject.instance()
    assert instance is not None
    instance.addMapLayer(layer)

    return layer


def remove_project_layer_by_source(
        source: str
):

    instance = QgsProject.instance()
    assert instance is not None

    for layer in instance.mapLayers().values():
        if Path(layer.source()) == Path(source):
            instance.removeMapLayer(layer.id())
