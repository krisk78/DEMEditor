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

    def __init__(self, canvas):
        super().__init__(canvas)

        self.points = []

        self.rubber_band = QgsRubberBand(
            canvas,
            QgsWkbTypes.PolygonGeometry # pyright: ignore[reportAttributeAccessIssue]
        )

        self.rubber_band.setColor(
            QColor(255, 0, 0, 120)
        )

        self.rubber_band.setWidth(2)

        self.selection_band = QgsRubberBand(
            canvas,
            QgsWkbTypes.PolygonGeometry # pyright: ignore[reportAttributeAccessIssue]
        )

        self.selection_band.setColor(
            QColor(0, 255, 0, 120)
        )

        self.selection_band.setWidth(3)


    def canvasPressEvent(self, e):

        if e is None:
            return

        if e.button() == Qt.MouseButton.LeftButton:

            point = self.toMapCoordinates(
                e.pos()
            )

            self.points.append(
                QgsPointXY(point)
            )

            self.update_polygon()


    def canvasReleaseEvent(self, e):

        if e is None:
            return
        
        if e.button() == Qt.MouseButton.RightButton:
            self.finish_polygon()


    def finish_polygon(self):

        if len(self.points) >= 3:

            geom = QgsGeometry.fromPolygonXY(
                [self.points]
            )

            print(
                "Polygone created :",
                geom.asWkt()
            )

            self.keep_selection()

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

        if self.selection_band:
            self.selection_band.reset(
                QgsWkbTypes.PolygonGeometry # pyright: ignore[reportAttributeAccessIssue]
            )


    def deactivate(self):

        self.reset()

        super().deactivate()


    def keep_selection(self):

        if len(self.points) < 3:
            return

        self.selection_band.reset(
            QgsWkbTypes.PolygonGeometry # pyright: ignore[reportAttributeAccessIssue]
        )

        for p in self.points:
            self.selection_band.addPoint(
                p,
                False
            )

        self.selection_band.addPoint(
            self.points[0],
            True
        )
