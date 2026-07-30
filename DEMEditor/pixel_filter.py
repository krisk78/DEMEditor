# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from .geom_processor import DEMGeometryProcessor

from abc import ABC, abstractmethod
from qgis.core import QgsPointXY, QgsGeometry, QgsRasterLayer


class PixelFilter(ABC):

    def __init__(self):
        self._full_raster = True

    def is_full_raster(self) -> bool:
        return self._full_raster

    def candidate_windows(self, layer: QgsRasterLayer) -> list[tuple[int, int, int, int]]:
        return [(0, layer.height(), 0, layer.width())]
    
    @abstractmethod
    def accept(self, row: int, col: int, value: float) -> bool:
        pass


class AndFilter(PixelFilter):

    def __init__(self, *filters: PixelFilter):
        super().__init__()
        self.filters = [f for f in filters if f is not None]

    def candidate_windows(self, layer: QgsRasterLayer) -> list[tuple[int, int, int, int]]:

        windows = []

        for f in self.filters:
            if f.is_full_raster():
                continue
            windows.extend(f.candidate_windows(layer))
            self._full_raster = False

        if not windows:
            return [(0, layer.height(), 0, layer.width())]
        
        return windows

    def accept(self, row: int, col: int, value: float) -> bool:
        return all(
            f.accept(row, col, value)
            for f in self.filters
        )


class FullRasterFilter(PixelFilter):

    def accept(self, row: int, col: int, value: float) -> bool:
        return True
    

class PolygonFilter(PixelFilter):

    def __init__(self, geometries: list[QgsGeometry]):

        super().__init__()
        if not geometries:
            raise ValueError("PolygonFilter requires at least one geometry")
        self._full_raster = False
        self.geometries = geometries

    def candidate_windows(self, layer: QgsRasterLayer) -> list[tuple[int, int, int, int]]:

        # Geometry is defined using project CRS
        DEMGeometryProcessor.validate_raster_context(layer)

        # clip geometry outside the layer extent
        self.geometries = DEMGeometryProcessor.clip_geometries(
            geometries=self.geometries,
            raster_layer=layer
        )

        candidate_windows = []

        extent = layer.extent()
        self.x_min = extent.xMinimum()
        self.y_max = extent.yMaximum()
        self.pixel_width = extent.width() / layer.width()
        self.pixel_height = extent.height() / layer.height()

        for geom in self.geometries:

            bbox = geom.boundingBox()
            candidate_windows.append(
                (
                    int((self.y_max - bbox.yMaximum()) / self.pixel_height),
                    int((self.y_max - bbox.yMinimum()) / self.pixel_height),
                    int((bbox.xMinimum() - self.x_min) / self.pixel_width),
                    int((bbox.xMaximum() - self.x_min) / self.pixel_width)
                )
            )

        return candidate_windows

    def accept(self, row: int, col: int, value: float) -> bool:

        x = self.x_min + (col + 0.5) * self.pixel_width

        y = self.y_max - (row + 0.5) * self.pixel_height

        point = QgsGeometry.fromPointXY(QgsPointXY(x, y))

        return any(
            geom.contains(point)
            for geom in self.geometries
        )
    

class ElevationFilter(PixelFilter):

    def __init__(
        self,
        min_elevation: float | None = None,
        max_elevation: float | None = None
    ):

        super().__init__()
        self.min_elevation = min_elevation
        self.max_elevation = max_elevation

    def accept(self, row: int, col: int, value: float) -> bool:

        if self.min_elevation is not None and value < self.min_elevation:
            return False

        if self.max_elevation is not None and value > self.max_elevation:
            return False

        return True
