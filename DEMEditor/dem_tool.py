# DEMEditor
# Copyright (C) 2026 Christophe Couaillet
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

from qgis.gui import QgsMapTool
from qgis.core import (
    QgsPointXY,
    QgsGeometry,
    QgsWkbTypes,
)
from qgis.gui import QgsRubberBand
from qgis.PyQt.QtCore import Qt
from qgis.PyQt.QtGui import QColor


class DEMPolygonTool(QgsMapTool):

    def __init__(self, canvas, on_polygon_created):
        super().__init__(canvas)

        self.map_canvas = canvas
        self.on_polygon_created = on_polygon_created
        self.points = []

        self.rubber_band = QgsRubberBand(
            self.map_canvas,
            QgsWkbTypes.PolygonGeometry # pyright: ignore[reportAttributeAccessIssue]
        )

        self.rubber_band.setColor(QColor(255, 0, 0, 120))
        self.rubber_band.setFillColor(QColor(255, 0, 0, 80))

        self.rubber_band.setWidth(2)

        self.selection_bands = []


    def canvasPressEvent(self, e):

        if e is None:
            return

        if e.button() == Qt.MouseButton.LeftButton:

            point = self.toMapCoordinates(e.pos())
            self.points.append(QgsPointXY(point))
            self.update_polygon()


    def canvasReleaseEvent(self, e):

        if e is None:
            return
        
        if e.button() == Qt.MouseButton.RightButton:
            self.finish_polygon()


    def finish_polygon(self):

        if len(self.points) >= 3:
            geom = QgsGeometry.fromPolygonXY([self.points])
            self.keep_selection(geom)

        self.points.clear()

        self.rubber_band.reset(
            QgsWkbTypes.PolygonGeometry # pyright: ignore[reportAttributeAccessIssue]
        )


    def update_polygon(self):

        self.rubber_band.reset(
            QgsWkbTypes.PolygonGeometry # pyright: ignore[reportAttributeAccessIssue]
        )

        for p in self.points:
            self.rubber_band.addPoint(
                p,
                False
            )

        if self.points:
            self.rubber_band.addPoint(
                self.points[0],
                True
            )


    def reset(self):

        self.points.clear()

        if self.rubber_band:
            self.rubber_band.reset(
                QgsWkbTypes.PolygonGeometry # pyright: ignore[reportAttributeAccessIssue]
            )

        self.clear_selections()


    def deactivate(self):

        self.rubber_band.reset(
            QgsWkbTypes.PolygonGeometry # pyright: ignore[reportAttributeAccessIssue]
        )
        self.points.clear()

        super().deactivate()


    def keep_selection(self, geom):

        if len(self.points) < 3 or self.rubber_band is None:
            return
        
        self.on_polygon_created(geom)

        # create permanent display band
        band = QgsRubberBand(
            self.map_canvas,
            QgsWkbTypes.PolygonGeometry # pyright: ignore[reportAttributeAccessIssue]
        )

        band.setColor(QColor(0, 255, 0, 120))
        band.setFillColor(QColor(0, 255, 0, 80))
        band.setWidth(3)
        band.setToGeometry(geom, None)

        self.selection_bands.append(band)


    def remove_last_selection(self):

        if self.selection_bands:
            band = self.selection_bands.pop()
            band.reset(
                QgsWkbTypes.PolygonGeometry # pyright: ignore[reportAttributeAccessIssue]
            )


    def clear_selections(self):

        for band in self.selection_bands:
            band.reset(
                QgsWkbTypes.PolygonGeometry # pyright: ignore[reportAttributeAccessIssue]
            )

        self.selection_bands.clear()
